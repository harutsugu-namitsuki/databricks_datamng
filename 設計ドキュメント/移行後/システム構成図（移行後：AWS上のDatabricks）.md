# システム構成図（移行後：AWS上のDatabricks）

このダイアグラムは「**どこに何があるか**」を示す物理的な構成図です。

## ステータス凡例

- 通常表記: 記載済み
- `（📝暗黙）`: 存在が前提だが詳細は省略
- `（🔧詳細設計）`: 詳細設計フェーズで追加予定
- `（⛔不要）`: 今回のプロジェクトでは使用しない

```mermaid
flowchart TB
  %% ============================
  %% Databricks Control Plane (SaaS)
  %% ============================
  ControlPlane["Databricks Control Plane<br/>(SaaS - Databricks管理)"]

  subgraph AWS["AWS Account / Region: ap-northeast-1"]
    
    %% --- VPC ---
    subgraph VPC["VPC (10.0.0.0/16)"]
      
      %% --- ルーティング（暗黙/詳細設計） ---
      IGW["IGW<br/>（📝暗黙）"]
      RouteTable["ルートテーブル<br/>（🔧詳細設計）"]
      
      subgraph PrivateSubnet["Private Subnet<br/>(10.0.1.0/24)"]
        DBXCompute["Databricks Compute<br/>(EC2 クラスタ)"]
        RDS[("RDS PostgreSQL<br/>(Northwind)")]
      end

      subgraph PublicSubnet["Public Subnet<br/>(10.0.0.0/24)"]
        NAT["NAT Gateway<br/>(インターネット接続用)"]
      end

      %% Security Groups
      SGdbx["SG: dbx-compute<br/>(Outbound: All)"]
      SGrds["SG: rds<br/>(Inbound: 5432 from dbx-compute)"]
      NACL["Network ACL<br/>（🔧詳細設計）"]
      
    end

    %% --- VPC外のAWSサービス ---
    S3[("S3 Bucket<br/>s3://lake-northwind/<br/>(Delta Lake)")]
    IAMRole["IAM Role<br/>(Instance Profile)<br/>S3 Read/Write権限"]
    Secrets[("AWS Secrets Manager<br/>or Databricks Secret Scope<br/>(DB接続情報)")]
    KMS["KMS<br/>（🔧詳細設計）"]
    CloudWatch[("CloudWatch<br/>(ログ/アラート)")]
    CloudTrail["CloudTrail<br/>（🔧詳細設計）"]
    EventBridge["EventBridge<br/>（🔧詳細設計）"]
    SNS["SNS<br/>(通知: ジョブ失敗時)"]
    
    %% --- 今回不要なサービス ---
    subgraph NotUsed["今回不要なサービス（⛔）"]
      IAMUser["IAM User<br/>（⛔移行後は不要）"]
      WAF["WAF<br/>（⛔不要）"]
      Lambda["Lambda<br/>（⛔不要）"]
      ECS["ECS/EKS<br/>（⛔不要）"]
      Redshift["Redshift/Athena<br/>（⛔不要）"]
      DynamoDB["DynamoDB<br/>（⛔不要）"]
      VPN["VPN/DirectConnect<br/>（⛔不要）"]
    end

  end

  %% ============================
  %% 接続線
  %% ============================
  
  %% Control Plane → Compute
  ControlPlane -->|"クラスタ管理"| DBXCompute
  
  %% Compute ↔ RDS
  DBXCompute --- SGdbx
  RDS --- SGrds
  DBXCompute -->|"TCP 5432<br/>(JDBC)"| RDS

  %% Compute → S3
  DBXCompute -->|"S3 API<br/>(HTTPS)"| S3
  
  %% IAM / Secrets / KMS
  DBXCompute -.->|"AssumeRole"| IAMRole
  IAMRole -.->|"権限付与"| S3
  DBXCompute -.->|"シークレット取得"| Secrets
  KMS -.->|"暗号化"| S3
  KMS -.->|"暗号化"| Secrets

  %% Monitoring
  DBXCompute -.->|"ログ送信"| CloudWatch
  CloudWatch -.->|"アラート発火"| SNS
  CloudTrail -.->|"API監査"| S3

  %% NAT / IGW (Internet)
  DBXCompute -.->|"外部通信"| NAT
  NAT -.-> IGW
  RouteTable -.-> PrivateSubnet
  RouteTable -.-> PublicSubnet
```

## 構成要素一覧

| カテゴリ | 要素 | 説明 | ステータス |
|---------|------|------|------------|
| **ネットワーク** | VPC | Databricks ComputeとRDSを同一VPCに配置 | ✅ |
| | Private Subnet | RDSとComputeを配置（インターネット非公開） | ✅ |
| | Public Subnet | NAT Gateway経由で外部通信 | ✅ |
| | Security Groups | RDSへのアクセスをCompute IPのみに制限 | ✅ |
| | IGW | VPCからインターネットへの出口 | 📝暗黙 |
| | ルートテーブル | サブネットごとの経路制御 | 🔧詳細設計 |
| | Network ACL | サブネットレベルのファイアウォール | 🔧詳細設計 |
| **コンピュート** | Databricks Compute | EC2ベースのSparkクラスタ | ✅ |
| | RDS PostgreSQL | ソースデータ（Northwind） | ✅ |
| **ストレージ** | S3 | データレイク（Delta Lake形式で保存） | ✅ |
| **セキュリティ** | IAM Role | S3アクセス権限（Instance Profile経由） | ✅ |
| | IAM User | 移行後はInstance Profileを使うため不要 | ⛔移行後不要 |
| | Secrets Manager | DB接続情報の安全な管理 | ✅ |
| | KMS | 暗号化キーの管理 | 🔧詳細設計 |
| **監視/運用** | CloudWatch | ログ収集・メトリクス監視 | ✅ |
| | SNS | ジョブ失敗時のメール/Slack通知 | ✅ |
| | CloudTrail | API呼び出しの監査ログ | 🔧詳細設計 |
| | EventBridge | イベント駆動のトリガー | 🔧詳細設計 |
| **今回不要** | WAF | Webアプリへのアクセスがないため | ⛔不要 |
| | Lambda | サーバーレス関数を使用しないため | ⛔不要 |
| | ECS/EKS | コンテナを使用しないため | ⛔不要 |
| | Redshift/Athena | Databricksを使用するため | ⛔不要 |
| | DynamoDB | NoSQLを使用しないため | ⛔不要 |
| | VPN/DirectConnect | オンプレ接続がないため | ⛔不要 |
