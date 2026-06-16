-- Step 4-1c: Unity Catalog サービスクレデンシャルを作成する
-- Story 1-6: NAT Gateway・RDS 時間制限運用
--
-- 実行前に以下を置換すること:
--   <AWSアカウントID>  →  実際の AWS アカウント ID（12桁の数字）
--
-- 実行環境: Databricks SQL エディタ

CREATE SERVICE CREDENTIAL `northwind-lambda-invoke-credential`
WITH (
  aws_iam_role.role_arn = 'arn:aws:iam::<AWSアカウントID>:role/northwind-uc-lambda-invoke-role'
)
COMMENT 'Lambda invoke for cleanup pipeline (Story 1-6)';

-- External ID を確認する
-- 表示された External ID を Step 4-1d で iam_trust_policy_uc_lambda_invoke.json に記入すること
DESCRIBE SERVICE CREDENTIAL `northwind-lambda-invoke-credential`;
