import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from api import trace

trace.start_trace("rec00001")
trace.record(trace.make_span("db", "h_list", "sql", tables=["products"]))
p = trace._events_path()
last = p.read_text(encoding="utf-8").strip().splitlines()[-1]
obj = json.loads(last)
assert obj["trace_id"] == "rec00001" and obj["tables"] == ["products"], obj
print("OK: record -> jsonl")
