import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from api import trace

trace.start_trace("abc12345")
s1 = trace.make_span("db", "h_list", "sql", detail="SELECT ...", tables=["products"], dur_ms=12.4)
assert s1["trace_id"] == "abc12345"
assert s1["span_id"] == "s001"
assert s1["tables"] == ["products"]
s2 = trace.make_span("http", "list_products", "http")
assert s2["span_id"] == "s002", s2
print("OK: span model")
