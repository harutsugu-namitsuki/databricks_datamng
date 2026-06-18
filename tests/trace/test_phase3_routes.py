"""Phase 3 結合検証：/trace/map・/trace/rollup と SSE pub/sub 配信。

SSE は TestClient のストリーミングだと同プロセスでハングしやすいため、
ルートが使う実際の配信経路（trace.subscribe / record→_publish）を
asyncio で直接検証する。HTTP越しの最終確認は Phase 5（ブラウザ）で行う。
"""
import sys, pathlib, asyncio
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from fastapi.testclient import TestClient
from api.main import app
from api import trace

# --- /trace/map と /trace/rollup（HTTP・高速・確実） ---
with TestClient(app) as client:
    m = client.get("/trace/map").json()
    assert len(m["columns"]) == 8, m["columns"]
    assert len(m["nodes"]) >= 21, len(m["nodes"])     # 完全カバレッジ化で増加（現状41）
    assert len(m["edges"]) >= 24, len(m["edges"])     # 同上（現状54）
    assert m.get("routes") and m.get("pages"), "routes/pages missing"
    assert "detail" in m["nodes"]["fetch"], "node detail missing"
    # /trace/rollup は list を返す（起動時 ingest 済みなら中身あり）。各要素の形を確認。
    rj = client.get("/trace/rollup?window=1h").json()
    assert isinstance(rj, list)
    assert all({"edge", "count", "avg_ms"} <= set(x) for x in rj), rj


# --- SSE 配信経路：subscribe → record → 購読キューに届く ---
async def _sse_delivery():
    trace.bind_loop(asyncio.get_running_loop())
    q = trace.subscribe()
    try:
        trace.start_trace("sse00001")
        trace.record(trace.make_span("http", "/api/x", "http"))
        span = await asyncio.wait_for(q.get(), timeout=2)
        assert span["trace_id"] == "sse00001" and span["kind"] == "http", span
    finally:
        trace.unsubscribe(q)


asyncio.run(_sse_delivery())

print("OK: phase3 routes (map / rollup / SSE pub-sub)")
