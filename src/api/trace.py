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
# スキーマ修飾(schema.table)・引用符・別名は落としてテーブル名だけ返す。
_TABLE_RE = re.compile(
    r"\b(?:FROM|JOIN|INTO|UPDATE)\s+([A-Za-z_][\w\.]*)",
    re.IGNORECASE,
)


def extract_tables(sql: str) -> list[str]:
    """SQL文から対象テーブル名を順序維持・重複排除で抽出する。
    1つも取れなければ ['不明'] を返す（要件 FR-T4）。"""
    if not sql:
        return ["不明"]
    found: list[str] = []
    for m in _TABLE_RE.finditer(sql):
        name = m.group(1).split(".")[-1].strip('"')
        if name and name.lower() not in {"select"} and name not in found:
            found.append(name)
    return found or ["不明"]
