flowchart LR
  src[(RDS PostgreSQL\nNorthwind: src)]
  dbx[Databricks\nNotebooks/Jobs\n(ELT)]
  s3[(S3 Data Lake\nDelta Lake)]
  b[Bronze (=raw)\nスナップショット/増分]
  s[Silver (=stg)\n整形/標準化]
  g[Gold (=mart)\n集計/提供]
  ops[(Ops\ningestion_log/dq_results/job_runs/lineage)]
  cons[利用者\n(Notebook/Databricks SQL/BI)]
  sec[Secrets\n(DB接続情報)]
  iam[IAM Role / Instance Profile\n(S3アクセス)]

  src -->|JDBC Extract| dbx
  sec --> dbx
  iam --> dbx

  dbx -->|Load| b
  b -->|Transform| s
  s -->|Transform| g
  dbx -->|運用ログ/品質結果| ops
  g --> cons
  ops --> cons
