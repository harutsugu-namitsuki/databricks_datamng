import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from api.trace import extract_tables

def check(sql, expected):
    got = extract_tables(sql)
    assert got == expected, f"\nSQL: {sql}\n期待: {expected}\n実際: {got}"

# FROM + 複数 JOIN
check(
    "SELECT p.* FROM products p LEFT JOIN categories c ON p.category_id=c.category_id "
    "LEFT JOIN suppliers s ON p.supplier_id=s.supplier_id",
    ["products", "categories", "suppliers"],
)
# INSERT INTO
check("INSERT INTO orders (order_id) VALUES (%s)", ["orders"])
# UPDATE
check("UPDATE products SET units_in_stock=%s WHERE product_id=%s", ["products"])
# 抽出不能 → 「不明」（要件 FR-T4）
check("SELECT 1", ["不明"])

print("OK: extract_tables")
