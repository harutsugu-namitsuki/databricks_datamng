"""操作トレース可視化システム — トレース中核。

責務:
- SQL からの対象テーブル抽出
- contextvar による「現在のトレース」管理
- span の生成と JSONL 追記
- SSE 購読者への配信（スレッド安全）
- ロールアップ集計
計測の失敗は決して被観測アプリを止めない（要件 FR-T6 / NFR-R1）。
"""

import asyncio
import contextvars
import itertools
import json
import re
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

# FROM / JOIN / INTO / UPDATE の直後に来るテーブル名を拾う。
# ダブルクオート識別子（"Order Details" 等）または通常識別子を捕捉し、
# スキーマ修飾(schema.table)・引用符・別名は落としてテーブル名だけ返す。
_TABLE_RE = re.compile(
    r'\b(?:FROM|JOIN|INTO|UPDATE)\s+("[^"]+"|[A-Za-z_][\w\.]*)',
    re.IGNORECASE,
)


def extract_tables(sql: str) -> list[str]:
    """SQL文から対象テーブル名を順序維持・重複排除で抽出する。
    1つも取れなければ ['不明'] を返す（要件 FR-T4）。

    ベストエフォートであり厳密なSQLパーサではない。文字列リテラルやコメント中の
    FROM 等を誤検出し得るが、抽出はトレース表示用ラベルに過ぎず、失敗しても
    被観測アプリを止めない（FR-T6 / NFR-R1）。"""
    if not sql:
        return ["不明"]
    found: list[str] = []
    for m in _TABLE_RE.finditer(sql):
        name = m.group(1).strip('"').split(".")[-1].strip('"')
        if name and name not in found:
            found.append(name)
    return found or ["不明"]


# ---------------------------------------------------------------------------
# span モデルと contextvar による「現在のトレース」管理
# ---------------------------------------------------------------------------

# 現在処理中のトレース文脈（middleware が設定、db.py 計装が参照）。
# async→threadpool 間も contextvars はコピーされるため sync エンドポイントからも見える。
_current = contextvars.ContextVar("trace_ctx", default=None)


class TraceCtx:
    """1リクエスト＝1トレースの文脈。span_id を採番する。"""
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self._seq = itertools.count(1)

    def next_span_id(self) -> str:
        return f"s{next(self._seq):03d}"


def new_trace_id() -> str:
    return uuid.uuid4().hex[:8]


def start_trace(trace_id: str | None = None) -> TraceCtx:
    ctx = TraceCtx(trace_id or new_trace_id())
    _current.set(ctx)
    return ctx


def current() -> "TraceCtx | None":
    return _current.get()


def make_span(layer: str, node: str, kind: str, *, detail: str = "",
              tables: list[str] | None = None, dur_ms: float = 0.0,
              status: str = "ok", parent: str = "root") -> dict:
    ctx = current()
    return {
        "trace_id": ctx.trace_id if ctx else new_trace_id(),
        "span_id": ctx.next_span_id() if ctx else "s001",
        "parent_span_id": parent,
        "ts": datetime.now().isoformat(timespec="milliseconds"),
        "layer": layer, "node": node, "kind": kind,
        "detail": detail, "tables": tables or [], "dur_ms": round(dur_ms, 2),
        "status": status,
    }


# ---------------------------------------------------------------------------
# JSONL 追記コレクタ ＋ SSE pub/sub（スレッド安全）
# ---------------------------------------------------------------------------

# 出力先: リポジトリ直下 trace_data/（db.py と同じ parents[2] 基準）
_DATA_DIR = Path(__file__).resolve().parents[2] / "trace_data"
_DATA_DIR.mkdir(exist_ok=True)
_write_lock = threading.Lock()

# SSE 購読者（可視化ビュー）の asyncio.Queue 群と、メインイベントループ参照。
_subscribers: set[asyncio.Queue] = set()
_loop: asyncio.AbstractEventLoop | None = None


def bind_loop(loop: asyncio.AbstractEventLoop) -> None:
    """起動時にメインイベントループを記録（worker thread から push するため）。"""
    global _loop
    _loop = loop


def _events_path() -> Path:
    return _DATA_DIR / f"events-{time.strftime('%Y%m%d')}.jsonl"


def record(span: dict) -> None:
    """span を JSONL に追記し、SSE 購読者へ push する。
    いかなる失敗もここで握りつぶす（被観測アプリを止めない: FR-T6）。"""
    try:
        line = json.dumps(span, ensure_ascii=False)
        with _write_lock:
            with _events_path().open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        _publish(span)
        _rollup_accumulate(span)  # Task 6.1 で本実装
    except Exception:
        pass


def _publish(span: dict) -> None:
    if not _loop:
        return
    for q in list(_subscribers):
        try:
            _loop.call_soon_threadsafe(q.put_nowait, span)
        except Exception:
            pass


def subscribe() -> asyncio.Queue:
    # subscribe/unsubscribe はイベントループ側スレッドで呼ばれ、_publish は
    # list(_subscribers) のスナップショットを取って worker thread から読むため、
    # 集合の更新にロックは不要（反復中の変更影響を受けない）。
    q: asyncio.Queue = asyncio.Queue(maxsize=1000)
    _subscribers.add(q)
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    _subscribers.discard(q)


# ---------------------------------------------------------------------------
# ロールアップ集計（スパン → 地図ノード → 地図エッジを時間バケットで計数）
# 可視化ビューと同一の full-path ロジックでエッジを点灯・計数し、履歴の
# エッジ ID（"from>to"）がビューの地図エッジと一致するようにする。
# ---------------------------------------------------------------------------

_MAP_PATH = _DATA_DIR.parent / "src" / "api" / "trace_map.json"
if not _MAP_PATH.exists():  # db.py 基準(parents[2]=repo root)からの絶対化に失敗した場合の保険
    _MAP_PATH = Path(__file__).resolve().parent / "trace_map.json"


def _load_map() -> dict:
    try:
        return json.loads(_MAP_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"nodes": {}, "edges": [], "routes": {}, "pages": {}}


_MAP = _load_map()
_EDGES = [tuple(e) for e in _MAP.get("edges", [])]
_LABEL2ID = {v["label"]: k for k, v in _MAP.get("nodes", {}).items()}

_WINDOW_SECS = {"10m": 600, "1h": 3600, "1d": 86400,
                "1w": 604800, "1m": 2592000, "1y": 31536000}

# (edge, minute_bucket) -> [count, dur_sum]
_edge_buckets: dict[tuple[str, int], list] = {}
# trace_id -> {"nodes": set, "edges": set(counted), "last": epoch}
_trace_state: dict[str, dict] = {}


def _nodes_for_span(span: dict) -> set:
    """1スパンが点灯させる地図ノード id 群（ビューの nodesForSpan と同一規則）。"""
    nodes: set = set()
    kind = span.get("kind")
    node = span.get("node", "")
    routes = _MAP.get("routes", {})
    pages = _MAP.get("pages", {})
    if kind == "http":
        screen = pages.get(span.get("page", ""))
        if screen:
            nodes.add(screen)
        nodes.add("fetch")
        nodes.add("cors")
        handler = routes.get(node)
        if not handler:  # 完全一致が無ければ最長プレフィックス
            cand = [k for k in routes if node.startswith(k)]
            if cand:
                handler = routes[max(cand, key=len)]
        if handler:
            nodes.add(handler)
    elif kind == "auth":
        nodes.add("auth")
    elif kind == "sql":
        nodes.add("db")
        nodes.add("pg")
        for name in span.get("tables", []):
            nid = _LABEL2ID.get(name)
            if not nid and ("t_" + name) in _MAP.get("nodes", {}):
                nid = "t_" + name
            if nid:
                nodes.add(nid)
    return nodes


def _span_minute(span: dict) -> int:
    """スパンの発生時刻を分バケット(epoch//60)に。replay でも正しい窓に入るよう ts を使う。"""
    try:
        return int(datetime.fromisoformat(span["ts"]).timestamp() // 60)
    except Exception:
        return int(time.time() // 60)


def _rollup_accumulate(span: dict) -> None:
    """同一トレースのスパンを貯め、両端が点灯した地図エッジを 1 回だけ計数する。"""
    try:
        tid = span.get("trace_id")
        if not tid:
            return
        st = _trace_state.get(tid)
        if st is None:
            st = {"nodes": set(), "edges": set(), "last": time.time()}
            _trace_state[tid] = st
        st["nodes"].update(_nodes_for_span(span))
        st["last"] = time.time()
        minute = _span_minute(span)
        dur = span.get("dur_ms", 0.0) or 0.0
        lit = st["nodes"]
        for a, b in _EDGES:
            if a in lit and b in lit:
                edge = f"{a}>{b}"
                if edge not in st["edges"]:
                    st["edges"].add(edge)
                    bk = _edge_buckets.setdefault((edge, minute), [0, 0.0])
                    bk[0] += 1
                    bk[1] += dur
        # 古いトレース状態を間引く（メモリ抑制）
        now = time.time()
        for t in [t for t, s in _trace_state.items() if now - s["last"] > 120]:
            _trace_state.pop(t, None)
    except Exception:
        pass


def rollup_for(window: str) -> list[dict]:
    """指定時間窓のエッジ別通過量（進行中バケットも含む: FR-S2）。"""
    secs = _WINDOW_SECS.get(window, 3600)
    cutoff = int((time.time() - secs) // 60)
    agg: dict[str, list] = {}
    for (edge, minute), (cnt, dur) in list(_edge_buckets.items()):
        if minute >= cutoff:
            a = agg.setdefault(edge, [0, 0.0])
            a[0] += cnt
            a[1] += dur
    return [{"edge": e, "count": c, "avg_ms": round(d / c, 2) if c else 0.0}
            for e, (c, d) in agg.items()]


def _rollup_reset() -> None:
    """テスト用初期化。"""
    _edge_buckets.clear()
    _trace_state.clear()


def ingest_events() -> int:
    """起動時に保持中の全 events-*.jsonl を読み、ロールアップを復元（FR-S2 起動時集計）。"""
    n = 0
    try:
        for p in sorted(_DATA_DIR.glob("events-*.jsonl")):
            for line in p.read_text(encoding="utf-8").splitlines():
                try:
                    _rollup_accumulate(json.loads(line))
                    n += 1
                except Exception:
                    continue
        _trace_state.clear()  # 復元後は per-trace 状態を破棄（以降の生計数と独立）
    except Exception:
        pass
    return n


def purge_old(days: int = 7) -> None:
    """保持期間を超えた古い events-*.jsonl を削除（NFR-O2）。"""
    try:
        import datetime as _dt
        cutoff = _dt.date.today() - _dt.timedelta(days=days)
        for p in _DATA_DIR.glob("events-*.jsonl"):
            try:
                d = _dt.datetime.strptime(p.stem.replace("events-", ""), "%Y%m%d").date()
                if d < cutoff:
                    p.unlink()
            except Exception:
                continue
    except Exception:
        pass
