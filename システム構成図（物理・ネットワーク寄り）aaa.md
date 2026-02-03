flowchart LR
  E1[外部実体: Northwind\n(RDS PostgreSQL)]
  P1((P1: 取り込み\nJDBC→Bronze))
  D1[(D1: Bronze\nDelta on S3)]
  P2((P2: 整形\nBronze→Silver))
  D2[(D2: Silver\nDelta on S3)]
  P3((P3: 提供用加工\nSilver→Gold))
  D3[(D3: Gold\nDelta on S3)]
  P4((P4: 品質検査))
  D4[(D4: Ops\nログ/品質/リネージ)]
  E2[利用者: Analyst/BI\nDatabricks SQL]

  E1 --> P1 --> D1 --> P2 --> D2 --> P3 --> D3 --> E2
  D2 --> P4 --> D4
  D3 --> P4
