"""Phase 2 結合検証（TestClient・別プロセス不要）。
中間者ミドルウェア・認証計装・db.py 計装が span を出すことを確認する。
ローカル PostgreSQL 稼働が前提。"""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from fastapi.testclient import TestClient
from api.main import app
from api import trace


def spans_for(trace_id):
    lines = trace._events_path().read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines if json.loads(l)["trace_id"] == trace_id]


with TestClient(app) as client:
    # 1) 公開API: http span + sql span が同一 trace_id で出る／認証spanは無い
    r = client.get("/api/categories", headers={"X-Trace-Id": "p2pub001"})
    assert r.status_code == 200, r.status_code
    s = spans_for("p2pub001")
    kinds = {x["kind"] for x in s}
    assert "http" in kinds, s
    assert "sql" in kinds, s
    assert "auth" not in kinds, s  # 公開APIは認証スキップ＝authノード不在
    sql = [x for x in s if x["kind"] == "sql"][0]
    assert "categories" in sql["tables"], sql
    http = [x for x in s if x["kind"] == "http"][0]
    assert http["node"] == "/api/categories" and http["status"] == "ok", http

    # 2) 保護API + 無効トークン: 認証 span が status=error で出る／401
    r = client.get("/api/employees", headers={"Authorization": "Bearer bad", "X-Trace-Id": "p2auth01"})
    assert r.status_code == 401, r.status_code
    s = spans_for("p2auth01")
    auth = [x for x in s if x["kind"] == "auth"]
    assert auth and auth[0]["status"] == "error", s
    http = [x for x in s if x["kind"] == "http"][0]
    assert http["status"] == "error", http  # 401 は http span も error

print("OK: phase2 integration (middleware / auth / db instrumentation)")
