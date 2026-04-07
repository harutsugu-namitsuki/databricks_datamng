# Databricks Solution Accelerators — ユースケース一覧

出典: [databricks.com/jp/solutions/accelerators](https://www.databricks.com/jp/solutions/accelerators) および [databricks-industry-solutions GitHub](https://github.com/databricks-industry-solutions)（計195リポジトリ）

調査日: 2026-03-29

---

## 全体サマリー

| 項目 | 内容 |
|------|------|
| 確認済みアクセラレーター数 | 120以上 |
| 対象業種 | 金融、小売・CPG、ヘルスケア・ライフサイエンス、製造、通信、メディア・エンタメ、ゲーム、サイバーセキュリティ、サプライチェーン、エネルギー、自動車、公共 |
| ユースケースカテゴリ | 予測、解約防止、不正検知、レコメンデーション、NLP/GenAI、コンピュータビジョン、地理空間、グラフ分析、IoT/ストリーミング、リスク管理、コンプライアンス、創薬、ゲノミクス、データ品質 |
| 共通技術スタック | Databricksノートブック（PySpark）、MLflow、Delta Lake |
| ノートブック取得方法 | GitHubからクローン or Databricks Reposへ1クリックインポート |

---

## 1. 金融サービス

| アクセラレーター名 | 説明 | ユースケースカテゴリ | 主要技術 |
|------------------|------|-------------------|---------|
| Fraud Detection | ルールベースAIモデルで金融詐欺に対抗。異常検知＋詐欺予測 | 不正・リスク | MLflow, Delta Lake |
| Anti-Money Laundering (AML) & KYC | マネーロンダリング防止とKYCコンプライアンス。数十億件のトランザクション異常検知 | コンプライアンス / リスク | Spark, Delta Lake |
| Market Risk | モンテカルロシミュレーションによるリスク管理近代化 | リスク管理 | Monte Carlo, Delta Lake |
| Credit Risk / Propensity Scoring | 効果的なプロペンシティスコアリングパイプライン。特徴量管理とモデルトラッキング | ML / 信用リスク | MLflow, Feature Store |
| Value at Risk (VaR) | モンテカルロシミュレーションによるVaR計算 | マーケットリスク | PySpark, MLflow |
| ESG Scoring | NLP＋ニュース分析によるESG取り組み抽出。サステナブルファイナンス | ESG / サステナビリティ | NLP, Delta Lake |
| Quant Beta / CAPM | 株式ベータ計算とCAPMモデル | 定量金融 | PySpark |
| Predicting Implied Volatility | オプションのインプライドボラティリティ予測 | 定量金融 | ML, PySpark |
| Nasdaq Crypto Analytics | Nasdaq Data Link デジタルアセットを使った投資インテリジェンス | 投資分析 | Delta Lake |
| Merchant Classification | MLベースの加盟店分類 | 決済分析 | NLP, ML |
| Geoscan Fraud | 地理空間分析による顧客行動理解と不正パターン検出 | 不正検知 | Geospatial, ML |
| Regulatory Reporting (reg-reporting) | Delta Live Tablesによるリアルタイム規制データ処理 | コンプライアンス | DLT, Spark Streaming |
| Transaction Embedding | 人口統計を超えた包括的な消費者プロファイル構築 | 顧客分析 | Embeddings, ML |
| FSI Model Risk Management Generation | LLMによるモデルリスク管理ドキュメント自動生成 | モデルガバナンス | LLMs, GenAI |
| Financial NLP / Company Ecosystem Graph | 金融テキストから企業エコシステムのナレッジグラフ構築 | NLP / ナレッジグラフ | John Snow Labs NLP |
| Insurance QA with NLP | NLPとHugging Faceによる保険請求処理のデジタル化 | 保険請求 | Hugging Face, Delta Lake |
| Smart Claims | 保険金請求管理の効率化、処理コスト削減、潜在的詐欺検出 | 保険請求 | ML, Delta Lake |
| Car Classification | 転移学習による保険会社向けコンピュータビジョン入門 | 保険 / コンピュータビジョン | Transfer Learning |
| Medical Risk Factors for Life Insurance | 生命保険引受のための医療リスク因子の自動抽出 | 保険引受 | NLP, John Snow Labs |
| Ship-to-Ship Transfer Detection | 地理空間分析による不正な船舶間転送の識別 | 不正 / コンプライアンス | Geospatial Analytics |
| Agent Bricks FinS MAG7 | 金融サービス向けエージェントAIシステム | GenAI / エージェントAI | Databricks Agents |

---

## 2. 小売・消費財

| アクセラレーター名 | 説明 | ユースケースカテゴリ | 主要技術 |
|------------------|------|-------------------|---------|
| Demand Forecasting | 店舗・商品単位の細粒度需要予測 | 予測 | Prophet, Spark |
| Many Model Forecasting (MMF) | 数千モデルへのスケーリングを可能にする大規模予測ソリューション | 予測 | MLflow, Hyperopt |
| Safety Stock | サプライチェーン全体の在庫バッファ推定 | 在庫最適化 | Optimization, Delta Lake |
| Customer Segmentation | 購買行動ベースの高度な顧客セグメント作成 | マーケティング分析 | ML, Delta Lake |
| RFM Segmentation | RFM（最新性・頻度・金額）分析による顧客ワークフロー最適化 | 顧客分析 | PySpark, ML |
| Customer Lifetime Value (CLV) | 将来の購買行動予測のためのCLV計算 | 顧客分析 | MLflow, Delta Lake |
| Predict Customer Churn | 顧客ライフタイム理解と解約予測 | 解約防止 | MLflow, Delta Lake |
| Survivorship and Churn | サブスクリプション解約分析。行動データからリスク顧客を特定 | 解約 / サブスクリプション | Survival Analysis, MLflow |
| Propensity Scoring | オファーへの顧客受容性推定。マーケティング最適化 | マーケティング分析 | MLflow, Feature Store |
| Product Recommendation (ALS) | 個人化された商品レコメンデーション向け行列分解 | レコメンデーション | ALS, Spark MLlib |
| Wide & Deep Recommender | 協調フィルタリングと再購入パターンを組み合わせたレコメンダー | レコメンデーション | TensorFlow, Spark |
| LLM Recommender | LLMベースの商品レコメンダー | レコメンデーション / GenAI | LLMs, Databricks |
| Image-Based Recommendations | Eコマース向け画像類似性レコメンデーション | レコメンデーション / CV | Computer Vision, Embeddings |
| Market Basket Analysis | 商品親和性を活用した個人化レコメンデーション | レコメンデーション | Spark MLlib |
| Point-of-Sale with DLT | Delta Live Tablesによるリアルタイム店舗内分析 | ストリーミング / 小売 | DLT, Spark Streaming |
| On-Shelf Availability | リアルタイムデータで欠品問題を解決 | 小売オペレーション | Spark Streaming, Delta |
| Optimized Order Picking | 倉庫ピッキング最適化ロジック | サプライチェーン / 運用 | Optimization |
| Fuzzy Item Matching | MLベースの商品マッチング | データ品質 | ML, NLP |
| Product Search | Databricks上でのセマンティック商品検索 | 検索 / NLP | Embeddings, Vector Search |
| Multi-Touch Attribution | 広告支出と売上を結びつけるマルチタッチアトリビューション | マーケティングアトリビューション | ML, Delta Lake |
| Causal Incentive | 因果推論による顧客インセンティブ投資最適化 | マーケティング / 因果AI | DoWhy, CausalML |
| AB Testing | A/Bテスト分析のための統計的フレームワーク | 実験・検証 | PySpark, Statistics |
| Customer Entity Resolution | テキスト属性とMLによる顧客レコードマッチング | データ品質 / MDM | ML, NLP |
| Clickstream Analytics | ユーザー行動とコンバージョン最適化のためのクリックストリーム分析 | デジタル分析 | Spark Streaming |
| Product Copy GenAI | 生成AIを使った商品コピー作成 | GenAI / マーケティング | LLMs, Databricks |
| Review Summarization | LLMによる商品レビューの自動分析 | GenAI / 分析 | LLMs, NLP |
| Intermittent Demand Forecasting | Nixtlaを使った間欠的需要予測 | 予測 | Nixtla, Spark |

---

## 3. メディア・エンタメ・ゲーム

| アクセラレーター名 | 説明 | ユースケースカテゴリ | 主要技術 |
|------------------|------|-------------------|---------|
| Video Streaming Quality of Experience | バッチ・ストリーミングデータ分析による動画配信品質の確保 | QoS / 視聴者離脱防止 | Spark Streaming, Delta |
| Recommendation Engines for Media | パーソナライズされたオムニチャネルレコメンデーション | コンテンツレコメンデーション | ALS, ML, Spark |
| Toxicity Detection in Gaming | NLPによるゲームチャットのリアルタイム有害言語検出 | 安全・信頼 | NLP, MLflow |
| Gamer Lifecycle | プレイヤーライフサイクル全体にわたるゲーマー行動分析 | プレイヤー分析 | ML, Delta Lake |
| Real-Time Bidding | プログラマティック広告最適化。インプレッション価値最大化 | アドテク | Spark Streaming, ML |
| Contextual Content Placement | コンテキスト認識型広告・コンテンツ配置最適化 | アドテク | ML, NLP |
| Media Mix Modeling | チャネル横断的なマーケティング支出効果測定と最適化 | マーケティング分析 | Bayesian, PyMC |
| Responsible Gaming | リスクのあるギャンブラーを特定・保護するための分析 | ゲームコンプライアンス | ML, Delta Lake |

---

## 4. ヘルスケア・ライフサイエンス

| アクセラレーター名 | 説明 | ユースケースカテゴリ | 主要技術 |
|------------------|------|-------------------|---------|
| FHIR Interoperability | FHIRヘルスケアデータの取り込みと分析。患者アウトカム分析 | ヘルスケア相互運用性 | FHIR, Delta Lake |
| HL7 Smolder | HL7v2電子カルテメッセージのApache Sparkデータソース | 医療データエンジニアリング | Spark, HL7 |
| Patient Risk Scoring | 疾患歴に基づく患者レベルリスクスコアリング | 臨床分析 | ML, Delta Lake |
| OMOP CDM | OMOP共通データモデルによるヘルスデータ活用 | ヘルスケア相互運用性 | OMOP, Delta Lake |
| Social Determinants of Health (SDOH) | 患者文書のフリーテキストから社会的決定要因を抽出 | 臨床NLP | NLP, Delta Sharing |
| Adverse Drug Events | 市販後の副作用イベント抽出・処理・分析 | 医薬品安全 | NLP, Delta Lake |
| Oncology Real-World Data | 非構造化リアルワールドデータからのNLPによるがん医療洞察生成 | オンコロジー分析 | NLP, John Snow Labs |
| Medicare Risk Adjustment | 非構造化臨床ノートからの未診断疾患の自動抽出 | 収益サイクル / リスク調整 | NLP, John Snow Labs |
| Medical Data De-identification | テーブル・文書・画像内のPHI検出と保護 | プライバシー / コンプライアンス | NLP, Computer Vision |
| Digital Pathology Image Analysis | AI搭載病理画像分析による診断ワークフロー強化 | 臨床AI / コンピュータビジョン | Deep Learning, Delta Lake |
| Genomics (Glow) | ゲノムワイド関連解析（GWAS）による遺伝的変異の特定 | ゲノミクス | Glow, PySpark |
| HLS Protein Folding | Databricks上でのタンパク質構造予測 | 創薬 | AlphaFold, Spark |
| AI-Driven Drug Discovery | AIを使った創薬サイクルの加速 | 創薬 | ML, Databricks |
| Medical Image Processing (DICOM) | 大規模医療画像処理。OHIF Viewer＋セグメンテーションモデル | 医療画像 | Computer Vision, Delta Lake |
| Clinical Notes Summarization | LLMによる臨床文書サマリー生成 | 臨床GenAI | LLMs, John Snow Labs |
| Building a RAG LLM Clinical Chatbot | オープンソースLLMを使った臨床文書QAシステム | 臨床GenAI / RAG | LLMs, RAG |
| Next Best Action for Pharma | 製薬営業向けネクストベストアクションレコメンデーション | 製薬営業分析 | ML, Delta Lake |
| HEDIS Score | HEDISヘルスケア品質スコア計算 | 医療品質 | PySpark, Delta |
| X12 EDI Parser | ヘルスケアトランザクション向けX12 EDIメッセージの読み書き | 医療データエンジニアリング | PySpark |

---

## 5. 製造・産業IoT

| アクセラレーター名 | 説明 | ユースケースカテゴリ | 主要技術 |
|------------------|------|-------------------|---------|
| Digital Twin | IoTセンサーデータを使ったデジタルツイン。リアルタイム構造・運用監視 | IoT / 予知保全 | Spark Streaming, AutoML |
| Factory Optimization (OEE) | エンドツーエンドの設備監視。OEE計算とスケーラビリティ | 製造分析 | DLT, Spark |
| Manufacturing Root Cause Analysis | DoWhyによる製造データの因果根本原因分析 | 品質 / RCA | DoWhy, 因果推論 |
| CV Quality Inspection | プリント基板品質検査のためのコンピュータビジョン。サーバーレス推論 | 品質管理 | Computer Vision, ML |
| IoT Distributed ML | IoT欠陥検知のためのML分散コード | IoT / ML | PySpark, MLflow |
| IoT Time Series Analysis | DLTとTempoを使ったIoTデータの時系列分析 | IoT分析 | DLT, Tempo |
| Comtrade Accelerator | COMTRADEフォーマットを使った電力ユーティリティの障害検出ストリーミングパイプライン | ユーティリティ / 障害検出 | Spark Streaming |
| Half-Hourly Energy Data | 30分単位のエネルギー消費分析 | エネルギー分析 | PySpark, Delta |
| LLMs for Manufacturing | 製造オペレーションと文書のためのLLMベースQAボット | GenAI / 製造 | LLMs, RAG |
| Rare Event Inspection | PyODライブラリを使ったスケールでの外れ値検出 | 異常検知 | PyOD, PySpark |
| Automotive Geospatial Accelerator | リアルタイム地理空間・テレマティクス・センサーデータによる道路安全とリスク防止 | 自動車 / テレマティクス | Geospatial, Spark Streaming |

---

## 6. サプライチェーン・物流

| アクセラレーター名 | 説明 | ユースケースカテゴリ | 主要技術 |
|------------------|------|-------------------|---------|
| Supply Chain Distribution Optimization | サプライチェーン配送を変革するAIブループリント。コスト削減と効率向上 | 最適化 | ML, Optimization |
| Supply Chain Optimization | エンドツーエンドのサプライチェーン最適化 | オペレーションズリサーチ | PySpark, ML |
| Supply Chain Stress Testing | サプライチェーンネットワークのスケールでのストレステスト。レジリエンス強化 | リスク / レジリエンス | Simulation, Spark |
| Routing Optimization | 配送ルート最適化によるスケーラブルなルート生成 | ラストマイル物流 | Optimization, PySpark |
| Fine-Grained Demand Forecasting | 店舗・商品レベルの細粒度需要予測 | 需要計画 | Prophet, MLflow |

---

## 7. 通信

| アクセラレーター名 | 説明 | ユースケースカテゴリ | 主要技術 |
|------------------|------|-------------------|---------|
| Telco Customer Churn Prediction | MLによる顧客解約予測。ネットワークレベルの解約シグナル向けグラフ分析 | 解約防止 | Graph Analytics, MLflow |
| Graph Analytics for Telco Churn | 解約予測のためのネットワークレベルグラフ分析 | 解約 / グラフ | GraphFrames, ML |
| Fraud Prevention in Telco | AI/BIダッシュボードを使ったエンドツーエンドの通信詐欺防止 | 不正検知 | ML, DLT |
| Telco Home Internet Threat Detection | 家庭用インターネット加入者のデバイス脅威検出 | サイバーセキュリティ | ML, Streaming |
| Telco Billing Customer Care | 課金分析と顧客ケア自動化 | CX / 課金 | ML, Delta Lake |
| Telco Reliability | ネットワーク信頼性の監視と分析 | ネットワーク運用 | Spark Streaming |

---

## 8. サイバーセキュリティ

| アクセラレーター名 | 説明 | ユースケースカテゴリ | 主要技術 |
|------------------|------|-------------------|---------|
| DNS Analytics | ペタバイト規模のDNSトラフィックログ全体での脅威検出と対応の加速 | 脅威検出 | Spark, Delta Lake |
| IOC Matching | インシデント対応者・脅威ハンター向けのIoCマッチング | 脅威インテリジェンス | PySpark, ML |
| Incident Investigation (Graphistry) | DatabricksとGraphistryを使ったサイバーセキュリティ調査の視覚的分析 | SIEM / ビジュアライゼーション | Graphistry, Spark |
| OCSF Schema Normalization | セキュリティイベントデータをOCSF標準に正規化するSQL/PySpark実装 | データエンジニアリング | PySpark, SQL |
| Insider Threat Risk | 行動分析を使ったインサイダー脅威リスクの検出とスコアリング | セキュリティ分析 | ML, Delta Lake |
| User Behavior Analytics for Cloud Services | クラウド環境での異常なユーザー行動検出 | UBA / UEBA | ML, Spark |
| Security Analysis Tool (SAT) | Databricksワークスペースのセキュリティ設定分析とベストプラクティス推奨 | セキュリティガバナンス | Python, REST API |

---

## 9. クロスインダストリー / GenAI・データエンジニアリング

| アクセラレーター名 | 説明 | ユースケースカテゴリ | 主要技術 |
|------------------|------|-------------------|---------|
| DIY LLM QA Bot | オープンソースLLMを使ったRAGアーキテクチャのカスタマーサービスQAボット構築 | GenAI / カスタマーサービス | LLMs, RAG, MLflow |
| Semantic Caching | FAQのLLM応答時間改善とAPIコスト削減のためのキャッシングシステム | GenAI / MLOps | Vector Store, LLMs |
| GraphRAG Demo | エンタープライズナレッジ向けグラフ強化RAG | GenAI / ナレッジグラフ | GraphRAG, LLMs |
| CSRD Regulatory Assistant | CSRD サステナビリティ報告規制ナビゲーションのためのGenAI＋RAG | 規制GenAI | RAG, LLMs |
| Auto Data Linkage | データセット間の自動リンクと重複排除 | データ品質 / MDM | ML, NLP |
| Geospatial H3 Visualization App | H3インデックスを使った地理空間分析・ビジュアライゼーション | 地理空間 | H3, Kepler.gl |
| Digitization of Documents | Apache TikaとTesseract OCRを使ったドキュメントからのテキスト抽出 | 非構造化データ | Tika, Tesseract |
| Email Customer Support Automation | LLMベースのメールカスタマーサポート自動化 | GenAI / CX | LLMs, Databricks |
| Prospect Analyzer | ウェブサイト分析・スコアリング・個人化アウトリーチのAI搭載B2B見込み客発掘 | 営業AI / GenAI | LLMs, Databricks |
| Sentiment Analyzer with AI Functions | Databricks AI Functionsを使ったセンチメント分析 | NLP / 分析 | AI Functions, SQL |
| AB Testing | 実験のための統計的テストフレームワーク | 実験・検証 | PySpark, Statistics |
| Transformer Forecasting | トランスフォーマーベースニューラルネットワークアーキテクチャによる予測 | ML / 予測 | Transformers, MLflow |
| Media Mix Modeling | マーケティング最適化のためのベイジアンメディアミックスモデリング | マーケティング分析 | PyMC, Bayesian |
| Survival Analysis | 時間-イベント予測のための生存分析統計手法 | ML / 分析 | PySpark, lifelines |
| Ray Framework on Databricks | Rayフレームワークを使った分散ML・AI | MLエンジニアリング | Ray, Databricks |
| Lakehouse Business Data Models | Lakehouse実装のためのビジネスデータモデルテンプレート | データアーキテクチャ | Delta Lake, SQL |
| DBX Metagen | DatabricksアセットのためのLLMによるメタデータ自動生成 | データガバナンス / カタログ | LLMs, Unity Catalog |
| DBX Redact | データリダクション・マスキングフレームワーク | データプライバシー | PySpark, Delta |

---

## 10. ユースケースカテゴリ別クロスリファレンス

### 予測・需要計画
- Demand Forecasting、Many Model Forecasting、Safety Stock、Fine-Grained Demand Forecasting、Intermittent Demand Forecasting、Transformer Forecasting、Parts Demand Forecasting

### 不正検知・リスク管理
- Fraud Detection（金融）、AML & KYC、Market Risk、Value at Risk、Geoscan Fraud、Telco Fraud Prevention、Ship-to-Ship Transfer Detection

### 解約防止・CX
- Predict Customer Churn、Survivorship and Churn、Telco Customer Churn Prediction、Gamer Lifecycle、Telco Billing Customer Care

### レコメンデーション
- Product Recommendation (ALS)、Wide & Deep Recommender、LLM Recommender、Image-Based Recommendations、Market Basket Analysis、Recommendation Engines for Media

### GenAI / LLM
- DIY LLM QA Bot、Semantic Caching、GraphRAG Demo、CSRD Regulatory Assistant、FSI Model Risk Management Generation、Clinical Notes Summarization、RAG Clinical Chatbot、LLMs for Manufacturing、Product Copy GenAI、Email Customer Support Automation、Prospect Analyzer

### NLP・テキスト分析
- Financial NLP、Insurance QA with NLP、Adverse Drug Events、Social Determinants of Health、Oncology Real-World Data、Game Review NLP、Review Summarization、Sentiment Analyzer

### コンピュータビジョン
- Digital Pathology、CV Quality Inspection、Car Classification、Medical Image Processing、Image-Based Recommendations、Computer Vision Foundations

### IoT・ストリーミング
- Digital Twin、IoT Time Series Analysis、IoT Distributed ML、Point-of-Sale with DLT、Telco Reliability、Video Streaming QoE

### 地理空間
- Geoscan Fraud、Geospatial H3 Visualization、Automotive Geospatial Accelerator

### サイバーセキュリティ
- DNS Analytics、IOC Matching、Insider Threat Risk、User Behavior Analytics、Security Analysis Tool

### ヘルスケア・ライフサイエンス特化
- FHIR Interoperability、OMOP CDM、Genomics (Glow)、AI-Driven Drug Discovery、HLS Protein Folding、HEDIS Score、X12 EDI Parser

---

*参照元: [github.com/databricks-industry-solutions](https://github.com/databricks-industry-solutions) (195リポジトリ), [databricks.com/jp/solutions/accelerators](https://www.databricks.com/jp/solutions/accelerators)*
