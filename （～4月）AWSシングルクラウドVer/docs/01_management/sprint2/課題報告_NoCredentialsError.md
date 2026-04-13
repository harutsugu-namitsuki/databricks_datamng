# 課題報告書: Databricks クラスター上の boto3 認証エラー

| 項目 | 内容 |
|------|------|
| 起票日 | 2026-04-13 |
| 更新日 | 2026-04-13 |
| 関連ストーリー | Story 1-6: NAT Gateway・RDS 時間制限運用 |
| ステータス | 対応中（対策C を採用、実装待ち） |

---

## 1. 発生事象

| 項目 | 内容 |
|------|------|
| **発生箇所** | `nb_06_cleanup.py`（Databricks ワークフロー最終タスク） |
| **エラー** | `botocore.exceptions.NoCredentialsError: Unable to locate credentials` |
| **発生タイミング** | `boto3.client("lambda")` で Lambda 関数を呼び出そうとした時点 |
| **影響範囲** | パイプライン完了後の自動クリーンアップ（RDS 停止 → NAT 削除）が実行不可 |

---

## 2. 根本原因

boto3 は EC2 インスタンスメタデータサービス（IMDS）から IAM 認証情報を取得するが、
Databricks クラスターの EC2 に **インスタンスプロファイルが付与されていない** ため、認証情報が存在しない。

### 原因の連鎖

| # | 原因 | 詳細 |
|---|------|------|
| 1 | CloudFormation にインスタンスプロファイル定義がない | `DatabricksWorkspaceRole`（IAM ロール）は作成済みだが、`AWS::IAM::InstanceProfile` リソースが未定義 |
| 2 | Databricks にインスタンスプロファイル未登録 | ワークスペース設定 → セキュリティ → インスタンスプロファイルに何も登録されていない |
| 3 | クラスターにインスタンスプロファイル未割当 | 登録がないため、クラスター設定の Advanced → Instance にドロップダウンが表示されない |

### 補足

- Unity Catalog 経由の S3 アクセス（Spark / Delta）は Catalog Role で動作しており正常
- 今回の問題は boto3 による **直接的な AWS API 呼び出し** に限定される
- クラスターのアクセスモードは **手動＋シングルユーザー（Dedicated）**

---

## 3. 対策案の評価

### 3.1 対策A: インスタンスプロファイルの作成・登録

**判定: ⚠️ 条件付きで実現可能（非推奨）**

| ステップ | 作業内容 | 実施場所 |
|----------|----------|----------|
| A-1 | 既存ワークスペースロール名を確認 | AWS IAM コンソール → ロール |
| A-2 | インスタンスプロファイルを作成 | AWS CLI（CloudShell） |
| A-3 | 既存ワークスペースロールをプロファイルに紐づけ | AWS CLI（CloudShell） |
| A-4 | Lambda Invoke ポリシーをロールに追加 | AWS IAM コンソール |
| A-5 | インスタンスプロファイル ARN を Databricks に登録 | Databricks 設定 → セキュリティ |
| A-6 | クラスター設定でインスタンスプロファイルを選択 | Databricks クラスター設定 → Advanced → Instance |

**重大リスク: クラスターアクセスモードの制約**

> **Standard アクセスモード（旧 Shared）のクラスターでは、IMDS へのアクセスがブロックされる。**
> インスタンスプロファイルを設定しても boto3 はクレデンシャルを取得できない。

| クラスターアクセスモード | 対策A の有効性 |
|--------------------------|---------------|
| Dedicated（Single User） | ✅ 有効 — 現在のクラスターはこのモードのため動作する |
| Standard（Shared） | ❌ 無効 — IMDS がブロックされるため根本的に機能しない |

根拠:
- Databricks 公式ドキュメント「Standard compute requirements and limitations」に明記
- Databricks KB「Unable to access secrets using instance profile in shared access mode」で同一エラーが報告

**メリット**: 認証情報の自動ローテーション、シークレット管理不要、コード変更なし
**デメリット**: Standard モードに移行した場合は再対応が必要、Databricks は非推奨方向、Serverless 非対応

---

### 3.2 対策B: Secret Scope + 明示的クレデンシャル

**判定: ✅ 実現可能だが非推奨（緊急回避策としてのみ許容）**

| ステップ | 作業内容 |
|----------|----------|
| B-1 | Lambda Invoke 権限を持つ IAM ユーザーを作成 |
| B-2 | アクセスキー / シークレットキーを発行 |
| B-3 | Databricks Secret Scope に格納 |
| B-4 | `nb_06_cleanup.py` を修正し、Secret Scope から認証情報を取得するよう変更 |

**デメリット**:
- アクセスキーの定期ローテーションが必要（AWS 推奨: 90日）
- コード変更あり
- セキュリティ的に非推奨（長期クレデンシャル）
- SOC2/ISO27001 等の監査で指摘対象

---

### 3.3 対策C: Unity Catalog サービスクレデンシャル（最推奨）

**判定: ✅ 実現可能・最推奨**

Databricks が 2025年に GA した **Unity Catalog サービスクレデンシャル** を使用する。
boto3 から AWS サービスを呼び出すための **Databricks 公式推奨メカニズム**。

根拠:
- Databricks 公式ドキュメント「Use Unity Catalog service credentials to connect to external cloud services」
- Standard アクセスモードの制限事項ドキュメントでも boto3 利用時の代替手段として明示的に案内

**前提条件**:

| 項目 | 必要条件 | 現状 |
|------|----------|------|
| Unity Catalog | ワークスペースで有効 | ✅ 充足済み（S3 アクセスで使用中） |
| Databricks Runtime | 16.2 以上（GA）/ 15.4 LTS 以上（Preview） | 要確認 |
| 権限 | `CREATE SERVICE CREDENTIAL` 権限 | メタストア管理者が保有 |

**実装ステップ**:

| ステップ | 作業内容 | 実施場所 |
|----------|----------|----------|
| C-1 | Lambda Invoke 権限を持つ IAM ロールを作成 | AWS CLI（CloudShell） |
| C-2 | Lambda Invoke ポリシーを作成・アタッチ | AWS CLI（CloudShell） |
| C-3 | Unity Catalog にサービスクレデンシャルを作成 | Databricks Catalog Explorer |
| C-4 | IAM ロールの信頼ポリシーを更新（External ID + Self-assuming） | AWS CLI（CloudShell） |
| C-5 | サービスクレデンシャルのバリデーション | Databricks Catalog Explorer |
| C-6 | 利用ユーザー/グループに ACCESS 権限を付与 | Databricks SQL |
| C-7 | `nb_06_cleanup.py` を修正 | Databricks ノートブック |

**アーキテクチャ**:

```
Databricks nb_06_cleanup.py
  │
  │ dbutils.credentials.getServiceCredentialsProvider(
  │     'northwind-lambda-invoke-credential')
  ▼
Unity Catalog Service Credential
  │
  │ (External ID で AssumeRole)
  ▼
AWS IAM Role: northwind-uc-lambda-invoke-role
  │
  │ lambda:InvokeFunction
  ▼
AWS Lambda: northwind-rds-stop / northwind-nat-delete
```

**メリット**: アクセスモード非依存、自動ローテーション、Unity Catalog ガバナンス（GRANT/REVOKE）、監査ログ対応、Serverless 対応

**デメリット**: コード変更あり（実質 5〜6 行）、DBR 15.4 LTS 以上が必要

---

## 4. 対策比較表

| 比較項目 | 対策A（インスタンスプロファイル） | 対策B（Secret Scope） | **対策C（サービスクレデンシャル）** |
|----------|----------------------------------|------------------------|-------------------------------------|
| Standard アクセスモード | ❌ 動作しない | ✅ | ✅ |
| Dedicated アクセスモード | ✅ | ✅ | ✅ |
| Serverless 対応 | ❌ | △ | ✅ |
| コード変更 | 不要 | あり | **5〜6行**（環境変数方式なら実質0行） |
| 認証情報の管理 | 自動ローテーション | 手動ローテーション | 自動ローテーション |
| Unity Catalog ガバナンス | ❌ | ❌ | ✅ |
| 監査ログ | EC2 レベル | なし | Unity Catalog 監査テーブルに記録 |
| 将来性 | Databricks は非推奨方向 | AWS が非推奨 | **Databricks 公式推奨** |

---

## 5. 推奨と現在のステータス

| 項目 | 内容 |
|------|------|
| **推奨** | **対策C（Unity Catalog サービスクレデンシャル）** |
| **現ステータス** | 対策C の実装準備中 |
| **前提確認** | Databricks Runtime バージョンが 15.4 LTS 以上であることを確認する |
| **次のアクション** | C-1（IAM ロール作成）から順次実施 |
| **手順書への反映** | 対策完了後に実装手順書（Story 1-6）へ追記予定 |

---

## 6. 旧報告書からの指摘事項（改訂で対応済み）

| # | 指摘 | 重要度 | 対応 |
|---|------|--------|------|
| 1 | クラスターアクセスモードの記載がなかった | Critical | 第2章に追記 |
| 2 | 対策C（サービスクレデンシャル）が検討されていなかった | Critical | 第3.3章に追加 |
| 3 | Databricks Runtime バージョンの記載がなかった | High | 第3.3章の前提条件に追記 |
| 4 | 対策A を無条件に推奨としていた | High | 条件付き（非推奨）に変更 |
| 5 | 対策B の位置づけが不明確だった | Medium | 「緊急回避策としてのみ許容」と明記 |

---

## 7. 対策C 詳細実装手順

詳細な実装手順は実施手順書の **Phase 4 Step 4-1** を参照:

`（新）Story1-6NAT Gateway時間制限運用実装手順書` → Phase 4: Step 4-1a〜4-1f

関連する外部ファイル一覧:

| ファイル | 用途 | 参照ステップ |
|----------|------|-------------|
| `iam_policy_uc_lambda_invoke.json` | UC サービスクレデンシャル用 IAM 許可ポリシー | Step 4-1a |
| `iam_trust_policy_uc_lambda_invoke_initial.json` | IAM ロール作成時に使う初期信頼ポリシー | Step 4-1b |
| `sql_4-1c_create_service_credential.sql` | サービスクレデンシャル作成 SQL | Step 4-1c |
| `iam_trust_policy_uc_lambda_invoke.json` | 最終信頼ポリシー（External ID 記入後に適用） | Step 4-1d |
| `nb_06_cleanup.py` | 修正済みクリーンアップノートブック（サービスクレデンシャル認証） | Step 4-2 |

---

## 8. 参照データソース

| # | ソース |
|---|--------|
| 1 | Databricks Docs: Standard compute requirements and limitations |
| 2 | Databricks Docs: Use Unity Catalog service credentials to connect to external cloud services |
| 3 | Databricks Docs: Create service credentials |
| 4 | Databricks Docs: Manage service credentials |
| 5 | Databricks KB: Unable to access secrets using instance profile in shared access mode |
| 6 | Databricks Community: DBUtils commands do not work on shared access mode clusters |
| 7 | Databricks Platform Release Notes |

---

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-04-13 | 初版作成（対策A・B のみ記載） |
| 2026-04-13 | 全面改訂: 対策C（サービスクレデンシャル）追加、対策A を条件付き非推奨に変更、アクセスモード制約・DBR バージョン要件を追記 |
| 2026-04-13 | セクション7 を刷新: インラインコードを全削除し、外部ファイル一覧と実施手順書への参照に統一（作成規約準拠） |
