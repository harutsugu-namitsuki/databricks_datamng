flowchart TB
  subgraph AWS["AWS Account / Region"]
    subgraph VPC["VPC（Databricks compute と RDS を同居させるのが最も簡単）"]
      DBXCompute[Databricks Compute\n(EC2 クラスタ)]
      RDS[(RDS PostgreSQL\nNorthwind)]
      SGdbx[Security Group: dbx-compute]
      SGrds[Security Group: rds]
      DBXCompute --- SGdbx
      RDS --- SGrds
      DBXCompute -->|TCP 5432| RDS
    end

    S3[(S3 Bucket\nData Lake/Delta)]
    IAMRole[IAM Role / Instance Profile\nS3 read/write]
    Secrets[(AWS Secrets Manager\nor Databricks Secret Scope)]
    Monitor[(監視/通知\nDatabricks Job通知 / CloudWatch等)]
  end

  ControlPlane["Databricks Control Plane\n(SaaS)"] --> DBXCompute
  DBXCompute -->|S3 API| S3
  DBXCompute --> IAMRole
  DBXCompute --> Secrets
  DBXCompute --> Monitor
