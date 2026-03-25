# Antigravityからの忠言: Story4-1～4-2実施手順書

`Story4-1～4-2実施手順書.md` に従って作業を進めるにあたり、以下の不都合（記載の誤り）と留意点があります。

## 🚨 最も重要な修正点：MLランタイムの必須要件

**【箇所】** Phase 1: Step 1-1 のノート
**【内容】** 
> 「既存クラスターが Standard Runtime の場合でも AutoML は動作するが」
と記載されていますが、これは誤りです。

**Databricks AutoML は `Databricks Runtime for Machine Learning (ML Runtime)` が必須要件（Required）**となっています。
Standard Runtime で UI から AutoML を実行しようとするとクラスターが選択できず、ノートブック（`databricks.automl`）から実行すると `databricks-automl-runtime` モジュールが見つからずエラー（`ImportError`）になります。

**【提案する修正】**
> 「AutoMLの実行には **Databricks Runtime ML** が必須です。Standard Runtimeでは動作しないため、必ずML Runtimeを選択したクラスターを利用してください」
という記述に修正することを強く推奨します。

---

## 💡 環境に依存する留意事項（不都合ではないが注意すべき点）

### 1. カタログ名のハードコード
各実行ノートブック（`nb_01_eda_data_overview.py` や `nb_02_automl_run.py`）の冒頭で `CATALOG_NAME = "northwind_catalog"` と直接指定されています。もし別のカタログ（例：devカタログなど）で検証を行う場合は、この変数を書き換えてください。

### 2. クラスターのアクセスモード（Access Mode）
AutoML を Unity Catalog 上のテーブルに対して実行する場合、クラスターのアクセスモードは原則として **「単一ユーザー（Single User）」** もしくはMLランタイムに対応した制限なしの共有（Shared）クラスターである必要があります。もしエラーが出た場合は Single User モードになっているか確認してください。

### 3. データリーケージの意図的な混入について
Phase 2 において `total_quantity`（注文数量）などが「リーケージの疑いあり」と正しく指摘されていますが、Phase 4 の学習用データセットにはそのまま含まれる構成になっています。「Story 4-3 でこれらを除外して再学習」と記載されているため、**「最初はわざとリーケージを含んだ高すぎる精度のモデルを作って見せ、後から直す」という教育的意図**であれば問題ありません。

---

## 💻 実行コード（ノートブック）に対する忠言

### 1. 時系列データ分割の考慮漏れ（`nb_02_automl_run.py`）
**【箇所】** セル 2 の `automl.regress()` 実行部分
**【内容】** 売上の予測のような時系列のデータにおいて、デフォルトのランダム分割（Random Split）を行うと、「未来のデータで過去を学習する」という深刻なデータリーケージが発生します。
**【提案する修正】**
AutoMLが時系列に従って、過去データで学習・未来データで検証できるよう、`time_col` 引数を追加することを強く推奨します。
```python
summary = automl.regress(
    dataset=df_train,
    target_col="total_sales",
    time_col="order_date",   # ← ★時系列分割のために追加推奨
    primary_metric="rmse",
    timeout_minutes=30,
    max_trials=20,
)
```

### 2. OOM（メモリ枯渇）リスクのある Pandas 変換（`nb_02_eda_sales_analysis.py`）
**【箇所】** セル 5 の相関行列計算 `pdf = ...toPandas()`
**【内容】** 今回の事前検証データ（Gold層テーブル）は件数が少ないため問題なく動きますが、実際の巨大な売上データで `.toPandas()` を実行すると、Driverノードのメモリが枯渇し（OOMエラー）、クラスタがクラッシュする危険があります。
**【提案する修正】**
より実戦的（スケーラブル）な書き方にするのであれば、以下のようにPySparkネイティブの相関関数を使用するか、サンプリングしてからPandasに変換するベストプラクティスをコメントで添えておくと親切です。
```python
# PySparkネイティブで相関を計算する場合
correlation = df_product.stat.corr("total_sales", "total_quantity")

# もしくはPandasを使う前にサンプリングする
pdf = df_product.select(...).sample(fraction=0.1).toPandas()
```
