```mermaid
sequenceDiagram
  autonumber
  participant W as Azure Databricks<br/>Workflow/Job（毎日）
  participant SEC as Databricks Secrets<br/>(認証情報管理)
  participant UC as Unity Catalog<br/>(メタデータ/リネージ)
  participant I as Ingest（JDBC→Bronze）
  participant INET as インターネット<br/>(TLS暗号化)
  participant P as RDS Postgres<br/>(AWS/Northwind)
  participant B as Bronze Delta<br/>(AWS S3)
  participant T as Transform（Silver/Gold）
  participant S as Silver Delta<br/>(AWS S3)
  participant G as Gold Delta<br/>(AWS S3)
  participant D as DQ Check
  participant O as Ops Tables<br/>(AWS S3/ログ/品質)
  participant CW as CloudWatch<br/>(🔧詳細設計)

  Note over W,CW: === 認証情報取得フェーズ ===
  W->>SEC: Access Key/DB認証情報を取得
  SEC-->>W: 認証情報を返却

  Note over W,CW: === Ingestフェーズ ===
  W->>I: run開始（run_id, load_date生成）
  I->>INET: JDBC over TLS (Port 5432)
  INET->>P: パブリックIP経由でRDS接続<br/>(SG: Azure IP許可)
  P-->>INET: テーブルデータ返却
  INET-->>I: データ受信
  
  I->>B: Bronzeへappend（_load_date等付与）<br/>(S3 API + Access Key)
  I->>UC: メタデータ登録（External Location）
  I->>O: ingestion_logに記録

  Note over W,CW: === Transformフェーズ ===
  W->>T: Silver/Gold変換を実行
  T->>B: Bronzeからデータ読込
  T->>S: Silverへ書込（クレンジング/標準化）
  T->>UC: Silverメタデータ登録
  T->>G: Gold（mart）生成
  T->>UC: Goldメタデータ登録

  Note over W,CW: === DQチェックフェーズ ===
  T->>D: DQルールを実行
  D->>O: dq_resultsに記録
  D->>UC: 品質メタデータ登録
  D-->>W: OKなら成功 / NGなら失敗

  Note over W,CW: === 監視連携（🔧詳細設計）===
  O-.->CW: ログ/メトリクス連携
  CW-.->CW: アラート発報（SNS経由）
  ```
