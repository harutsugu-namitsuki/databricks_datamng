# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Northwind Data Lakehouse — a reference implementation of Databricks + Unity Catalog on AWS using the medallion architecture (Bronze/Silver/Gold). The primary working variant is **AWSシングルクラウドVer/** (AWS single-cloud). A secondary **マルチクラウドVer/** (Azure Databricks) variant also exists.

There is no build system, test runner, or package manager. All executable code runs as Databricks notebooks (PySpark) on a live Databricks workspace.

## Notebook Execution Order

Notebooks in `AWSシングルクラウドVer/開発ドキュメント/notebooks/` must be run in this order:

| Notebook | Timing | Purpose |
|----------|--------|---------|
| `00_setup_unity_catalog.py` | One-time | Create External Locations + Schemas in Unity Catalog |
| `01_load_northwind_to_rds.py` | One-time | Load Northwind SQL (14 tables) from GitHub into RDS PostgreSQL |
| `02_etl_bronze_ingest.py` | Daily | JDBC (RDS → Bronze Delta) with metadata columns |
| `03_etl_silver_transform.py` | Daily | Cleanse, type-convert, DQ checks → Silver |
| `04_etl_gold_aggregate.py` | Daily | Aggregate → 4 Gold marts |

## Architecture

```
AWS RDS PostgreSQL (private subnet)
    ↓ JDBC
Databricks Compute (EC2, customer-managed VPC)
    ↓ Unity Catalog + IAM
S3 (Delta Lake)
    ├── Bronze/   raw, append-only, +metadata cols (_run_id, _load_date, _ingest_ts, _source_system)
    ├── Silver/   cleansed, type-safe, DQ-checked
    ├── Gold/     4 aggregated business marts
    └── Ops/      logs, DQ results, job run history
```

**Two-role IAM design:**
- **Catalog Role** — S3 access, trusted by UCMasterRole (Unity Catalog)
- **Workspace Role** — EC2 cluster management, cross-account trust with Databricks control plane

**VPC layout:** Two private subnets (EC2 + RDS), one public subnet with NAT Gateway, S3 VPC Gateway Endpoint. Security groups enforce Databricks requirements (egress 443, 3306, 8443–8451).

## Key Files

| Path | Purpose |
|------|---------|
| `AWSシングルクラウドVer/開発ドキュメント/cloudformation.yaml` | IaC for VPC, RDS, S3, IAM roles, Security Groups |
| `AWSシングルクラウドVer/開発ドキュメント/実装手順書.md` | 5-phase implementation guide (authoritative execution reference) |
| `AWSシングルクラウドVer/設計ドキュメント/UnityCatalog設計書.md` | Unity Catalog namespace structure |
| `AWSシングルクラウドVer/設計ドキュメント/権限設計.md` | IAM role permission details |
| `AWSシングルクラウドVer/設計ドキュメント/テーブル設計書.md` | Delta table schemas for all layers |

## Data Source

Northwind database (14 tables) from [pthom/northwind_psql](https://github.com/pthom/northwind_psql):
- **Masters (7):** categories, customers, employees, suppliers, shippers, products, region
- **Transactions (2):** orders (~830 rows), order_details (~2,155 rows)
- **Configs (5):** territories, us_states, employee_territories, customer_demographics, customer_customer_demo

## Secrets

RDS credentials are stored in **AWS Secrets Manager** and accessed via **Databricks Secret Scope**. Never hardcode credentials in notebooks.

## `skills/` Directory

The `skills/` subdirectory contains cloned third-party Claude skill repositories (agentkits-marketing, claude-skills, Product-Manager-Skills, etc.). These are reference materials unrelated to the Databricks project.
