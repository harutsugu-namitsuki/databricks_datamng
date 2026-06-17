"""操作トレース可視化システム — トレース中核。

責務:
- SQL からの対象テーブル抽出
- contextvar による「現在のトレース」管理
- span の生成と JSONL 追記
- SSE 購読者への配信（スレッド安全）
- ロールアップ集計
計測の失敗は決して被観測アプリを止めない（要件 FR-T6 / NFR-R1）。
"""

import re

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

import contextvars
import itertools
import time
import uuid

# 現在処理中のトレース文脈（middleware が設定、db.py 計装が参照）。
# async→threadpool 間も contextvars はコピーされるため sync エンドポイントからも見える。
_current = contextvars.ContextVar("trace_ctx", default=None)


class TraceCtx:
    """1リクエスト＝1トレースの文脈。span_id を採番する。"""
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self._seq = itertools.count(1)
        self.last_span_id = "root"

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
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()) +
              f".{int((time.time() % 1) * 1000):03d}",
        "layer": layer, "node": node, "kind": kind,
        "detail": detail, "tables": tables or [], "dur_ms": round(dur_ms, 2),
        "status": status,
    }
