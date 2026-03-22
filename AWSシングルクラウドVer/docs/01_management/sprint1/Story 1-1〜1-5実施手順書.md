# パイプライン冪等化と自動化 実施手順書（Epic 1 / Sprint 1）

## 概要

| 項目 | 内容 |
|-----|------|
| 対象 Story | 1-1, 1-2, 1-3, 1-4, 1-5 |
| Epic | Epic 1: パイプラインの仕上げと自動化 |
| 目的 | Bronze→Silver→Gold パイプラインを冪等化し、日次自動実行・通知を設定する |
| 前提 | Phase 5（ETLパイプライン）完了済み。全テーブルが Bronze/Silver/Gold/Ops に存在すること |

### 関連ノートブック

| ノートブック | 用途 |
|------------|------|
| `docs/03_development/00_初期環境構築手順_インフラ/notebooks/02_etl_bronze_ingest.py` | Bronze取り込み（冪等化済み: `replaceWhere` で当日分上書き） |
| `docs/03_development/00_初期環境構築手順_インフラ/notebooks/03_etl_silver_transform.py` | Silver変換（冪等化済み: `dropDuplicates` 追加済み） |
| `docs/03_development/00_初期環境構築手順_インフラ/notebooks/04_etl_gold_aggregate.py` | Gold集計（`mode("overwrite")` で冪等） |

### 前提条件チェック

Databricks ノートブック上で以下を実行し、全テーブルが存在することを確認する。

`nb_00_prerequisite_check.py`

---

## Phase 1: Bronze 層冪等化（Story 1-1）

### 目的

現在の `02_etl_bronze_ingest.py` は `mode("append")` を使用しているため、同じ日に2回以上実行するとレコードが重複する。`_load_date` パーティション単位で上書きする方式に変更し、冪等性を確保する。

### Step 1-1: 現状の重複確認

Bronze 層の状態を確認する。

`nb_e1_00_duplicate_check.py`

- セル1: `_load_date` 別件数
- セル2: 主キー重複件数（`[DUP]` 表示があれば過去データに問題あり）

### Step 1-2: 冪等性の動作確認

1. `nb_e1_01_verify_idempotency.py`（セル1）を実行 → 件数を記録
2. `02_etl_bronze_ingest.py` を実行（1回目）
3. `nb_e1_01_verify_idempotency.py`（セル1・セル2）を実行 → 件数確認
4. `02_etl_bronze_ingest.py` を**もう一度**実行（2回目）
5. `nb_e1_01_verify_idempotency.py`（セル1・セル2）を再実行 → **2回目と件数が同じであること**を確認

`nb_e1_01_verify_idempotency.py`

---

## Phase 2: Silver 層冪等化（Story 1-2）

### 目的

`03_etl_silver_transform.py` は `mode("overwrite")` に加え、Bronze 読み込み直後に `dropDuplicates()` を追加済み。Bronze の冪等化（Story 1-1）完了後に動作確認する。

> **Gold層**: `04_etl_gold_aggregate.py` はすでに `mode("overwrite")` を使用しており、Silver が冪等であれば自動的に冪等となる。

### Step 2-1: Silver/Gold 冪等性の確認

1. `03_etl_silver_transform.py` を実行
2. `04_etl_gold_aggregate.py` を実行
3. 以下のノートブックで Silver 主キー重複がないことを確認する

`nb_e1_01_verify_idempotency.py`（セル3）

---

## Phase 3: Databricks Workflows 設定（Story 1-3）

### 目的

Bronze→Silver→Gold の3ノートブックを順番に実行する日次 Job を Databricks Workflows で設定する。

### Step 3-1: Job の作成

1. Databricks UI 左メニューから **Workflows** を開く
2. **Create job** をクリック
3. Job 名を入力: `northwind_daily_pipeline`

### Step 3-2: タスクの追加（3タスク）

以下の順番でタスクを追加する。

#### タスク1: bronze_ingest

| 設定項目 | 値 |
|---------|-----|
| Task name | `bronze_ingest` |
| Type | Notebook |
| Source | Workspace |
| Path | `<ワークスペース内の 02_etl_bronze_ingest.py のパス>` |
| Cluster | ※ Step 4-1 で Job Cluster に変更 |

#### タスク2: silver_transform

| 設定項目 | 値 |
|---------|-----|
| Task name | `silver_transform` |
| Type | Notebook |
| Source | Workspace |
| Path | `<ワークスペース内の 03_etl_silver_transform.py のパス>` |
| Depends on | `bronze_ingest` |
| Cluster | ※ Step 4-1 で Job Cluster に変更 |

#### タスク3: gold_aggregate

| 設定項目 | 値 |
|---------|-----|
| Task name | `gold_aggregate` |
| Type | Notebook |
| Source | Workspace |
| Path | `<ワークスペース内の 04_etl_gold_aggregate.py のパス>` |
| Depends on | `silver_transform` |
| Cluster | ※ Step 4-1 で Job Cluster に変更 |

### Step 3-3: スケジュール設定

1. **Add schedule** をクリック
2. 以下の通り設定する

| 設定項目 | 値 |
|---------|-----|
| Trigger type | Scheduled |
| Schedule | 毎日 02:00（JST） |
| Quartz cron 式 | `0 0 2 * * ?` |
| Timezone | Asia/Tokyo |

### Step 3-4: 手動実行テスト

1. **Run now** をクリックして手動実行する
2. 3タスクが順に `Running` → `Succeeded` になることを確認する（**スクリーンショット取得**）
3. 以下のノートブックで実行ログを確認する

`nb_e1_02_job_run_log_check.py`

---

## Phase 4: Job Cluster への切り替え（Story 1-4）

### 目的

All-Purpose クラスターは常時起動しているためコストが高い。Job 実行時のみ起動・終了する **Job Cluster** に切り替えることでコストを約30%削減できる。

### Step 4-1: 各タスクの Compute 設定変更

Job 編集画面で各タスクを選択し、以下の設定を行う。

**タスクごとに繰り返す（bronze_ingest / silver_transform / gold_aggregate）:**

1. タスクをクリック → **Cluster** 欄の編集ボタンをクリック
2. **Create new job cluster** を選択
3. 以下のパラメータを設定する

| 設定項目 | 値 |
|---------|-----|
| Databricks Runtime | `15.4.x-scala2.12`（LTS 推奨） |
| Worker type | `m5d.large`（AWS 汎用 / 安価） |
| Workers | `1`（Northwind 程度のデータ量では十分） |
| Driver type | Same as worker |
| Auto Termination | ジョブ完了後に自動終了（デフォルト） |

> **参考コスト比較**:
> - All-Purpose (`m5d.large` 常時起動 24h): 約 $1.40/日
> - Job Cluster (`m5d.large` 実行時のみ 約30分): 約 $0.03/日

4. 設定後 **Confirm** をクリック

### Step 4-2: 動作確認

1. Job を **Run now** で実行し、新規クラスターが起動することを確認する
2. 完了後にクラスターが自動終了することを確認する（**スクリーンショット取得**）

---

## Phase 5: メール通知設定（Story 1-5）

### 目的

Job の成功・失敗時にメール通知を受け取れるようにする。障害時に即座に検知できるようにする。

### Step 5-1: 通知設定

1. Job 編集画面の **Notifications** タブをクリック
2. **Add notification** をクリック
3. 以下の通り設定する

| 通知タイミング | 設定内容 |
|-------------|---------|
| On failure | 自分のメールアドレスを入力 |
| On success | 任意（学習環境では不要でも可） |
| On start | 任意 |

> **補足**: 通知メールは Databricks から `noreply@databricks.com` の差出人で送信される。迷惑メールフォルダに入る場合は許可リストに追加すること。

### Step 5-2: 通知の動作確認

1. Job を実行し、完了後にメールが届くことを確認する
2. 意図的にエラーを発生させてテストする場合は、ノートブック先頭に `raise Exception("test")` を一時追加し、失敗通知が届くことを確認する（確認後は削除）

---

## 注意事項

| 項目 | 内容 |
|------|------|
| replaceWhere の前提 | `_load_date` カラムが全 Bronze テーブルに存在すること（`02_etl_bronze_ingest.py` で付与済み） |
| 初回実行時 | テーブルが存在しない場合は `replaceWhere` が使えないため、初回は通常の `saveAsTable` で作成される |
| Shared クラスター | Shared クラスターではシングルユーザーモードの一部機能が使えない場合があるため、Job Cluster は Assigned (Single User) を推奨 |
| ジョブ実行順序 | silver_transform は bronze_ingest 完了後に開始する設定になっていること（依存関係の確認必須） |
| Gold層の冪等性 | `04_etl_gold_aggregate.py` はすでに `mode("overwrite")` を使用しており修正不要 |
| Story 1-6 | NAT Gateway の時間制限運用はフィージビリティ確認が必要なため Sprint 1 対象外 |

---

## 実施順序まとめ

```
Phase 1（Story 1-1）: Bronze冪等化
  └── Step 1-1（現状確認）→ Step 1-2（動作確認）
        ↓
Phase 2（Story 1-2）: Silver冪等化
  └── Step 2-1（動作確認）
        ↓
Phase 3（Story 1-3）: Workflows Job設定
  └── Step 3-1（Job作成）→ Step 3-2（タスク追加）→ Step 3-3（スケジュール）→ Step 3-4（手動実行テスト）
        ↓
Phase 4（Story 1-4）: Job Cluster切り替え
  └── Step 4-1（Compute設定変更）→ Step 4-2（動作確認）
        ↓
Phase 5（Story 1-5）: メール通知設定
  └── Step 5-1（通知設定）→ Step 5-2（動作確認）
```

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-03-22 | 初版作成。Story 1-1〜1-5 を Sprint 1 に組み込み |
