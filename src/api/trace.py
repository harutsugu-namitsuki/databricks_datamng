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
