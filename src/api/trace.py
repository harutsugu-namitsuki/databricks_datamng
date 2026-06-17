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


# Task 6.1 までの暫定スタブ（後で本実装に置換）
def _rollup_accumulate(span: dict) -> None:
    pass
