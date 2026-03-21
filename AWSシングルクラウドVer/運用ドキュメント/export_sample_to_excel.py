"""
サンプルデータCSVを1つのExcelブックに統合するスクリプト

出力イメージ:
  シート「bronze→」(空) → 「categories」→ 「customers」→ ...
  シート「silver→」(空) → 「customers」→ 「order_details」→ ...
  シート「gold→」(空)   → 「order_summary」→ ...
  シート「ops→」(空)    → 「dq_results」→ ...
"""

import os
import glob
import pandas as pd
from pathlib import Path

# ---------- 設定 ----------
SCRIPT_DIR = Path(__file__).resolve().parent

# サンプルデータフォルダを自動検出（最新のものを使用）
sample_dirs = sorted(SCRIPT_DIR.glob("サンプルデータ_*"))
if not sample_dirs:
    raise FileNotFoundError("サンプルデータフォルダが見つかりません")
SAMPLE_DIR = sample_dirs[-1]  # 最新を使用

# レイヤー定義（表示順）
LAYERS = ["bronze", "silver", "gold", "ops"]

# 出力ファイル
OUTPUT_FILE = SCRIPT_DIR / f"サンプルデータ統合_{SAMPLE_DIR.name.split('_', 1)[1]}.xlsx"

# ---------- メイン処理 ----------
def find_csv(table_dir: Path) -> Path | None:
    """テーブルフォルダ内のCSVファイルを取得する"""
    csvs = list(table_dir.glob("*.csv"))
    return csvs[0] if csvs else None


def collect_tables(layer_dir: Path) -> list[tuple[str, Path]]:
    """レイヤーフォルダ配下のテーブル一覧を取得する（ソート済み）

    bronze/ の下にさらに bronze/ がネストしている構造にも対応
    """
    if not layer_dir.exists():
        return []

    # サブフォルダを探索
    candidates = sorted(layer_dir.iterdir())
    tables = []

    for entry in candidates:
        if not entry.is_dir():
            continue
        csv = find_csv(entry)
        if csv:
            tables.append((entry.name, csv))
        else:
            # 1段深いネスト（例: bronze/bronze/categories/）
            for sub in sorted(entry.iterdir()):
                if sub.is_dir():
                    csv = find_csv(sub)
                    if csv:
                        tables.append((sub.name, csv))

    return tables


def main():
    print(f"サンプルデータフォルダ: {SAMPLE_DIR}")
    print(f"出力先: {OUTPUT_FILE}")

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        sheet_count = 0

        for layer in LAYERS:
            layer_dir = SAMPLE_DIR / layer

            # レイヤー区切りシート（空）
            separator_name = f"{layer}→"
            pd.DataFrame().to_excel(writer, sheet_name=separator_name, index=False)
            sheet_count += 1
            print(f"  シート: {separator_name} (区切り)")

            # テーブルごとにシート作成
            tables = collect_tables(layer_dir)
            for table_name, csv_path in tables:
                df = pd.read_csv(csv_path)
                df.to_excel(writer, sheet_name=table_name, index=False)
                sheet_count += 1
                print(f"  シート: {table_name} ({len(df)} 行)")

    print(f"\n完了: {sheet_count} シートを出力しました → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
