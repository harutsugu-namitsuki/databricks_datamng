"""Task 6.1 ロールアップ：スパン→地図エッジの計数がビューと同じエッジIDになることを確認。"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from api import trace

trace._rollup_reset()

# 1トレース：http(GET /api/products, 画面=store/catalog.html) と sql(db.py, tables=[products])
trace.start_trace("t1")
sp = trace.make_span("http", "/api/products", "http", dur_ms=5.0)
sp["page"] = "store/catalog.html"   # Referer 末尾2セグメント
sp["method"] = "GET"                 # メソッド+パスでハンドラ照合
trace.record(sp)
trace.record(trace.make_span("db", "db.py", "sql", tables=["products"], dur_ms=3.0))

r = trace.rollup_for("1h")
edges = {e["edge"]: e["count"] for e in r}

# full-path ロジックで点灯する地図エッジが計数されている（ビューと同じID体系）
for must in ["catalog>fetch", "fetch>cors", "cors>h_list", "h_list>db", "db>pg", "pg>t_products"]:
    assert must in edges, f"missing edge {must} in {edges}"
# 同一トレース内の各エッジは1回だけ
assert all(v == 1 for v in edges.values()), edges

# 別トレースを足すと count が増える
trace.start_trace("t2")
sp2 = trace.make_span("http", "/api/products", "http", dur_ms=4.0)
sp2["page"] = "store/catalog.html"; sp2["method"] = "GET"
trace.record(sp2)
trace.record(trace.make_span("db", "db.py", "sql", tables=["products"], dur_ms=2.0))
edges2 = {e["edge"]: e["count"] for e in trace.rollup_for("1h")}
assert edges2["pg>t_products"] == 2, edges2

# 窓が短すぎる(10m)でも今のバケットは含まれる（進行中=途中経過）
assert any(e["edge"] == "fetch>cors" for e in trace.rollup_for("10m"))

print("OK: rollup (map-edge counting / window)")
