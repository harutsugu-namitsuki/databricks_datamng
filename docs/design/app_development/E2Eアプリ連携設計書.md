# E2E アプリ連携設計書

アプリ層（EC ストア / 業務管理）での操作が、**RDS → 日次 ETL → データレイクハウス（Bronze/Silver/Gold）
→ BI** までどう伝わるかを定義する。アプリ単体の設計は [システム設計.md](システム設計.md)、画面は
[画面設計.md](画面設計.md) を参照。

## 連携の全体像

```
[アプリ操作]            [同期]                [非同期：日次ETL]            [活用]
EC 注文 / 商品登録 ──▶ RDS PostgreSQL ──JDBC──▶ Bronze → Silver → Gold ──▶ BI / 在庫アラート
在庫調整               (即時反映)              (1日1回バッチ)             (翌日以降に反映)
```

**重要な性質：データの流れは現状一方通行**（アプリ → RDS → レイクハウス）。
Gold の分析結果をアプリに戻す経路（レコメンド・需要予測に基づく推奨発注など）は未実装で、
将来の「活性化層（逆ETL）」の検討対象。

## シナリオ 1：EC 注文の E2E

図: [注文連携シーケンス.puml](注文連携シーケンス.puml)

### 同期フェーズ（リアルタイム・[create_order](../../../src/api/main.py)）

1. 顧客がカートを確定（配送先・配送業者を選択）
2. ブラウザが `POST /api/orders`（Bearer トークン + 明細）
3. FastAPI がセッションから `customer_id` を取得（store ログイン必須、未ログインは 403）
4. `SELECT MAX(order_id)+1` で採番
5. `orders`（ヘッダ）を INSERT
6. 明細ごとに `order_details` を INSERT し、`products.units_in_stock` を数量分減算
7. `{ ok, order_id }` を返し、画面は注文履歴へ遷移

### 非同期フェーズ（日次バッチ）

8. 翌日の ETL が RDS から `orders`/`order_details`/`products` を Bronze に取り込み
9. Silver でクレンジング・型変換・DQ チェック（`line_total` 計算等）
10. Gold で `sales_by_product` / `sales_by_customer` / `sales_by_category` / `order_summary` を更新
11. BI に売上が反映。`units_in_stock <= reorder_level` の商品は在庫アラート対象に

## シナリオ 2：業務管理の更新の E2E

| アプリ操作 | RDS（同期） | レイクハウス（翌日） |
|---|---|---|
| 商品の新規登録 / 編集 | `products` INSERT / UPDATE | Gold の商品マスタ・売上集計に反映 |
| 在庫調整（`/api/inventory/adjust`） | `products.units_in_stock` UPDATE | 在庫アラート判定が更新 |
| 従業員情報の編集 | `employees` UPDATE | （PII はマスキング方針に従う） |

## データ整合性・制約

| 観点 | 現状 | 留意点 / 将来対応 |
|---|---|---|
| 反映タイミング | 日次バッチ | アプリの更新は**当日中は BI に出ない**（最大 ~1 日のラグ） |
| トランザクション境界 | orders/order_details/在庫の複数文が単一 Tx で囲われていない | 途中失敗で**部分反映**の恐れ。本番化時は 1 トランザクション化が必要 |
| order_id 採番 | `MAX(order_id)+1` | 同時注文で**採番競合**の可能性。シーケンス/採番テーブル化を検討 |
| 固定値 | `employee_id=1`, `freight=0`, `discount=0` を固定 | 実運用では担当者割当・運賃計算・値引ロジックが必要 |
| 在庫の負値 | `/api/inventory/adjust` は負値を拒否、注文時の減算はチェックなし | 注文時も在庫引当・下限チェックを入れるべき |
| 冪等性 | 無し | 二重 POST で二重注文の恐れ。べき等キー等を検討 |

> これらは「PoC として動く」状態の既知の割り切り。商社向けに本番化／仕入・配送を足す段階で、
> トランザクション設計と採番設計を見直す（→ 概念データモデルの「在庫移動履歴」「発注」エンティティと接続）。

## 関連ドキュメント

- アプリ設計: [システム設計.md](システム設計.md) / [画面設計.md](画面設計.md)
- アーキ図: [アプリ層アーキテクチャ.puml](アプリ層アーキテクチャ.puml)
- データ層: [テーブル設計書.md](../data_platform/テーブル設計書.md) / [概念データモデル.puml](../data_platform/概念データモデル.puml)
- メダリオン: [メダリオンアーキテクチャ設計書.md](../data_platform/メダリオンアーキテクチャ設計書.md)
