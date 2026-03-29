# 機械学習モデル構築 実施手順書（Epic 4 / Story 4-1, 4-2）

## 概要

| 項目 | 内容 |
|-----|------|
| 対象 Story | 4-1（EDA・特徴量決定）, 4-2（AutoML ベースラインモデル生成） |
| Epic | Epic 4: 機械学習モデルの構築と管理 |
| 目的 | Gold 層の売上データを探索的に分析し、Databricks AutoML でベースラインモデルを自動生成する |
| 前提 | Epic 1（パイプライン自動化）完了済み。Gold 層の 4 テーブルにデータが存在すること |

### 予測テーマ

| 項目 | 内容 |
|-----|------|
| 予測対象 | 商品別の月次売上金額（`total_sales`） |
| 粒度 | 商品 × 月（`gold.sales_by_product` の 1 行 = 1 サンプル） |
| 問題の種類 | 回帰（Regression） |

### 使用するテーブル

| テーブル | 層 | 用途 |
|---------|-----|------|
| `northwind_catalog.gold.sales_by_product` | Gold | EDA の主要データソース・学習データのベース |
| `northwind_catalog.gold.sales_by_customer` | Gold | 顧客分析（EDA 参考） |
| `northwind_catalog.gold.sales_by_category` | Gold | カテゴリ別トレンド（EDA 参考） |
| `northwind_catalog.gold.order_summary` | Gold | 日次注文サマリ（EDA 参考） |
| `northwind_catalog.silver.products` | Silver | カテゴリ・単価情報（特徴量結合用） |
| `northwind_catalog.silver.categories` | Silver | カテゴリ名（特徴量結合用） |

### ノートブック一覧

| ファイル | Story | 用途 |
|---------|-------|------|
| `notebooks_sprint3/story4-1/nb_01_eda_data_overview.py` | 4-1 | Gold 層テーブルの概要・件数・基本統計量の確認 |
| `notebooks_sprint3/story4-1/nb_02_eda_sales_analysis.py` | 4-1 | 時系列トレンド・分布・相関分析・特徴量決定 |
| `notebooks_sprint3/story4-2/nb_01_automl_data_prep.py` | 4-2 | 学習データセットの作成と保存 |
| `notebooks_sprint3/story4-2/nb_02_automl_run.py` | 4-2 | AutoML 実験の実行と結果確認 |

---

## Phase 1: EDA - データ概要の把握（Story 4-1 前半）

### 目的

Gold 層マートテーブルの基本統計量・データ分布を把握し、機械学習に使えるデータかどうかを判断する。

### Step 1-1: Compute（クラスター）の起動

1. Databricks UI 左メニューから **「コンピューティング」（Compute）** をクリック
2. 既存の All-Purpose クラスターを **「開始」（Start）** する
3. ステータスが **Running** になるまで待つ

> **ML ランタイム必須**: AutoML の実行には **Databricks Runtime ML（Machine Learning）** が必須です。Standard Runtime では `databricks.automl` モジュールが存在せず `ImportError` となり動作しません。クラスター作成時に必ず ML Runtime を選択してください。
>
> **アクセスモード**: AutoML を Unity Catalog テーブルに対して実行する場合、クラスターのアクセスモードは **「単一ユーザー（Single User）」** である必要があります。共有クラスターでエラーが出た場合はアクセスモードを確認してください。

### Step 1-2: Gold 層テーブルの概要確認

以下のノートブックを Databricks ワークスペースにインポートして実行する。

`notebooks_sprint3/story4-1/nb_01_eda_data_overview.py`

各セルの確認ポイント：

| セル | 確認内容 | 着目点 |
|------|---------|--------|
| セル1 | Gold 層 4 テーブルの件数・カラム数 | データ量が学習に十分か |
| セル2 | `sales_by_product` のスキーマとサンプル | カラムの型・値の範囲 |
| セル3 | 基本統計量（mean, stddev, min, max） | 外れ値の有無 |
| セル4 | データ期間と商品数・月数 | 学習データの時間幅 |
| セル5 | 商品ごとのレコード数 | 全期間にデータがある商品の割合 |
| セル6 | NULL・ゼロ値の件数 | 欠損の影響 |
| セル7 | `order_summary` の概要 | 日次粒度の傾向 |

---

## Phase 2: EDA - 売上分析と特徴量検討（Story 4-1 後半）

### 目的

時系列トレンド・分布・相関を分析し、予測対象（target）と特徴量（features）を決定する。

### Step 2-1: 売上分析ノートブックの実行

以下のノートブックをインポートして実行する。

`notebooks_sprint3/story4-1/nb_02_eda_sales_analysis.py`

各セルの確認ポイント：

| セル | 分析内容 | 着目点 |
|------|---------|--------|
| セル1 | 月別売上推移（全体） | トレンド（上昇/下降）・季節性の有無 |
| セル2 | カテゴリ別売上推移 | カテゴリ間の差異・成長カテゴリ |
| セル3 | 商品別売上分布 | 売上の偏り（パレート分析） |
| セル4 | 売上上位 10 商品の月次推移 | 個別商品のトレンド変動 |
| セル5 | 相関行列 | `total_sales` と他カラムの相関の強さ |
| セル6 | 月別平均売上（季節性） | 特定月に売上が集中するか |
| セル7 | 顧客別売上分布 | 上位顧客への依存度 |
| セル8 | 国別売上 | 地域的な偏り |
| セル9 | 特徴量候補のまとめ | 予測対象と特徴量の最終決定 |

### Step 2-2: EDA 結論の確認

セル 9 の出力結果を確認する。以下の項目が決定されていること。

| 決定事項 | 期待値 |
|---------|--------|
| 予測対象（Target） | `total_sales`（商品別月次売上金額） |
| 予測粒度 | 商品 × 月 |
| 特徴量候補 | `product_name`, `order_year`, `order_month`, `category_name`, `unit_price` 等 |
| リーケージ注意カラム | `total_quantity`, `order_count`（target と強い相関） |

> **リーケージ（Data Leakage）とは**: 予測時には知り得ない情報が特徴量に含まれること。`total_quantity`（注文数量）は `total_sales`（売上金額）とほぼ同義のため、本番推論では使えない可能性がある。AutoML の Feature Importance で判断する。

---

## Phase 3: AutoML 用学習データの準備（Story 4-2 前半）

### 目的

EDA で決定した特徴量をもとに、AutoML に入力する学習データセットを作成し、Unity Catalog テーブルとして保存する。

### Step 3-1: データ準備ノートブックの実行

以下のノートブックをインポートして実行する。

`notebooks_sprint3/story4-2/nb_01_automl_data_prep.py`

| セル | 処理内容 | 確認ポイント |
|------|---------|-------------|
| セル1 | `gold.sales_by_product` の読み込み | 件数の確認 |
| セル2 | 特徴量エンジニアリング（カテゴリ・単価の結合、日付列の追加） | スキーマ・サンプルデータの確認 |
| セル3 | `gold.ml_training_sales` テーブルとして保存 | 保存成功メッセージの確認 |
| セル4 | 保存データの基本統計量 | 異常値がないこと |

### Step 3-2: 学習データの確認

保存されたテーブルを Catalog Explorer（カタログエクスプローラー）で確認する。

1. Databricks UI 左メニューから **「カタログ」（Catalog）** をクリック
2. `northwind_catalog` → `gold` → `ml_training_sales` を選択
3. **「サンプルデータ」（Sample Data）** タブでデータを確認
4. **「詳細」（Details）** タブでスキーマ・行数を確認

---

## Phase 4: AutoML 実験の実行（Story 4-2 後半）

### 目的

Databricks AutoML を使って、学習データに対する回帰モデルを自動生成する。

### Step 4-1: AutoML の実行方法を選択する

AutoML は **2 つの方法** で実行できる。どちらか一方を選択する。

| 方法 | 特徴 | 推奨 |
|------|------|------|
| **方法 A: UI から実行** | コードなし、設定画面で操作 | 初回はこちらが分かりやすい |
| **方法 B: ノートブックから実行** | `databricks.automl` API を使用 | 再現性が高い |

### Step 4-2A: UI から AutoML を実行する場合

1. Databricks UI 左メニューから **「実験」（Experiments）** をクリック
2. **「AutoML 実験を作成」（Create AutoML Experiment）** をクリック
3. 以下の設定を入力する

| 設定項目 | 値 |
|---------|-----|
| クラスター（Cluster） | Step 1-1 で起動したクラスター |
| ML の問題の種類（ML problem type） | **回帰（Regression）** |
| 入力テーブル（Input training dataset） | `northwind_catalog.gold.ml_training_sales` |
| 予測対象（Prediction target） | `total_sales` |
| 評価指標（Evaluation metric） | `rmse`（Root Mean Squared Error） |
| タイムアウト（Timeout） | `30 分` |

4. **「AutoML を開始」（Start AutoML）** をクリック
5. 実験が完了するまで待つ（通常 10〜30 分）

### Step 4-2B: ノートブックから AutoML を実行する場合

以下のノートブックをインポートして実行する。

`notebooks_sprint3/story4-2/nb_02_automl_run.py`

> **注意**: セル 2 の `automl.regress()` は実行に 10〜30 分かかる。タイムアウトせずに完了を待つこと。

### Step 4-3: AutoML 結果の確認

AutoML 実験が完了したら、以下を確認する。

1. **「実験」（Experiments）** 画面で実験結果を開く
2. 各試行（Trial）が一覧表示される

| 確認項目 | 確認方法 |
|---------|---------|
| ベストモデルの RMSE | 試行一覧の上位（最小 RMSE） |
| ベストモデルの R² スコア | 1.0 に近いほど良い |
| Feature Importance | ベストモデルの Run をクリック → **「アーティファクト」（Artifacts）** |
| 生成ノートブック | 試行をクリック → **「ソースノートブック」（Source Notebook）** リンク |

3. **生成ノートブック** を開き、AutoML が自動生成したコードを確認する

> **ポイント**: AutoML が生成するノートブックは完全に編集可能。Story 4-3 ではこのノートブックをカスタマイズしてモデルを改善する。

### Step 4-4: Feature Importance の確認

ベストモデルの MLflow Run 画面で Feature Importance（特徴量の重要度）を確認する。

1. 実験画面でベストモデルの Run をクリック
2. **「アーティファクト」（Artifacts）** タブを開く
3. `feature_importance.png` または SHAP プロットを確認する

| 確認ポイント | 対処 |
|-------------|------|
| `total_quantity` や `order_count` の重要度が極端に高い | リーケージの疑い → Story 4-3 でこれらを除外して再学習 |
| `product_name` が上位 | 商品固有の特性を捉えている（正常） |
| `order_month` が上位 | 季節性を捉えている（正常） |

---

## Phase 5: 動作確認

### Step 5-1: Story 4-1 の完了確認

| # | 確認項目 | 期待結果 |
|---|---------|---------|
| 1 | `nb_01_eda_data_overview.py` が正常に実行された | 全セルがエラーなく完了 |
| 2 | `nb_02_eda_sales_analysis.py` が正常に実行された | 全セルがエラーなく完了 |
| 3 | 予測対象が決定された | `total_sales`（商品別月次売上） |
| 4 | 特徴量候補が決定された | セル 9 の出力に一覧が表示される |

### Step 5-2: Story 4-2 の完了確認

| # | 確認項目 | 期待結果 |
|---|---------|---------|
| 1 | `gold.ml_training_sales` テーブルが作成された | Catalog Explorer（カタログエクスプローラー）で確認可能 |
| 2 | AutoML 実験が完了した | Experiments（実験）画面に結果が表示される |
| 3 | ベストモデルの RMSE / R² が表示される | メトリクスが数値で表示される |
| 4 | Feature Importance が確認できる | アーティファクトに画像・プロットが存在する |
| 5 | AutoML 生成ノートブックが存在する | リンクからノートブックを開ける |

### Step 5-3: 証跡の記録

1. EDA ノートブックの実行結果（主要グラフ）のスクリーンショットを取得する
2. AutoML 実験結果画面のスクリーンショットを取得する
3. Feature Importance プロットのスクリーンショットを取得する
4. ベストモデルのメトリクス画面のスクリーンショットを取得する

> **保存先**: `docs/01_management/sprint3/証跡/` 配下に保存する。

---

## 完了チェックリスト

| Story | 完了条件 | 確認 |
|-------|---------|------|
| 4-1 | Gold 層データの EDA が完了し、予測対象（`total_sales`）と特徴量候補が決定された | ☐ |
| 4-2 | AutoML 実験が完了し、ベースラインモデルのメトリクス（RMSE, R²）が記録された | ☐ |
| 共通 | スクリーンショットによる証跡が記録されている | ☐ |

---

## 次のステップ

| Story | 内容 | 依存 |
|-------|------|------|
| 4-3 | AutoML 生成ノートブックをカスタマイズし、モデルを改善する | 4-2 完了後 |
| 4-4 | MLflow で実験パラメータ・メトリクス・アーティファクトをトラッキングする | 4-3 完了後 |
| 4-5 | モデルを MLflow Model Registry（Unity Catalog）に登録する | 4-4 完了後 |
| 4-6 | 登録モデルでバッチ推論を実行し、結果を Gold 層に保存する | 4-5 完了後 |
