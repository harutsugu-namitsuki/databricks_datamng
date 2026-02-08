# データフロー（移行前：Azure Databricks → AWS）

移行前（暫定構成）のデータフローを示すシーケンス図です。
Azure DatabricksからAWS RDS/S3に接続するクロスクラウド構成です。

```mermaid
sequenceDiagram
  autonumber
  %% --- 登場人物（データ/システム）の定義 ---
  box "Azure環境 (Databricks)" #e3f2fd
    participant DBX as Azure Databricks<br/>(Compute)
    participant Unity as Unity Catalog<br/>(メタデータ)
  end

  box "AWS環境" #fff3e0
    participant RDS as RDS<br/>(Northwind)
    participant Bronze as Bronze<br/>(S3 Delta)
    participant Silver as Silver<br/>(S3 Delta)
    participant Gold as Gold<br/>(S3 Delta)
  end

  box "Ops & Governance" #e8f5e9
    participant Ops as Ops<br/>(Logs/DQ)
  end

  %% --- 処理フロー ---
  Note over DBX, Gold: 日次バッチ処理開始

  %% 0. メタデータ確認
  DBX->>Unity: 0. テーブル定義確認
  Unity-->>DBX: メタデータ返却

  %% 1. Ingest (インターネット経由)
  DBX->>RDS: 1. JDBC接続 (インターネット経由/SSL)
  RDS-->>DBX: データ返却
  DBX->>Bronze: 2. データ保存 (S3 API + Access Key)
  activate Bronze
  Bronze->>Ops: 3. ログ記録 (Ingestion Log)
  DBX->>Unity: 3b. メタデータ登録
  deactivate Bronze

  %% 2. Transform
  Bronze->>Silver: 4. クレンジング・標準化
  activate Silver
  Silver->>Ops: 5. 品質チェック (DQ Check)
  DBX->>Unity: 5b. リネージ記録
  
  opt 品質チェックNGの場合
      Ops-->>Silver: 処理中断 / アラート通知
  end
  deactivate Silver

  %% 3. Aggregate
  Silver->>Gold: 6. 集計・マート作成
  activate Gold
  Gold-->>Ops: 7. 完了記録
  DBX->>Unity: 7b. リネージ記録
  deactivate Gold
```

## 移行前の注意点

1. **クロスクラウド構成**: Azure Databricks から AWS RDS/S3 に接続
2. **JDBC接続はインターネット経由**: RDSのパブリックエンドポイントを使用
3. **SSL必須**: `sslmode=require` を接続文字列に含める
4. **S3接続はAccess Key**: IAM User の Access Key を Databricks Secrets に保存
5. **Unity Catalog**: メタデータ管理とリネージ追跡に使用

## Unity Catalog の役割

| 機能 | 説明 |
|------|------|
| **メタデータ管理** | テーブル/カラムの定義、説明 |
| **リネージ** | データの出自・変換履歴 |
| **アクセス制御** | ユーザー/グループ単位の権限管理 |
| **データ発見** | カタログ検索によるテーブル発見 |
