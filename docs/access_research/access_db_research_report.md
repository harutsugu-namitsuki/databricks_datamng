# Accessデータベース（Database1.accdb）システム構造 調査レポート

指定された `Database1.accdb`（C:\Users\YuenongMei(梅月濃)\OneDrive - 株式会社Dirbato\ドキュメント\Database1.accdb） を解析用スクリプト（COMオブジェクトを利用）で内部解析した結果、このファイルは単なるデータ格納庫ではなく、**Microsoft Accessの機能をフル活用して構築された「業務アプリケーション（システム）」** であることが判明しました。

以下に、なぜシステムとして動作するのか、およびその構成や実装内容について徹底調査した結果をご報告します。

---

## 1. なぜ「ただのDB」ではなく「システム」として立ち上がるのか？

Accessファイルをダブルクリックした際に、テーブル一覧などの編集画面ではなく「システム（アプリケーション画面）」が立ち上がるのは、以下の設定が組み込まれているためです。

* **AutoExec マクロの存在**: データベース内に `AutoExec` という名前のマクロが存在します。Accessはファイル起動時にこのマクロを自動的に実行する仕様になっており、このマクロ内で初期画面（Home画面やLoginダイアログなど）を開くように設定されています。
* **スタートアップフォーム**: `Startup Screen` や `Home`, `Login Dialog` といったフォーム（画面）が存在し、これらがユーザーに提供される最初のインターフェースとして機能しています。
* **UIの制御**: 裏側で動作するVBAプログラムにより、標準のAccessメニュー（リボンやナビゲーションペイン）を非表示にし、ユーザーには専用の画面しか見えないように制御されている可能性が高いです。

---

## 2. 実装技術とプラットフォーム

* **プラットフォーム**: Microsoft Access (デスクトップデータベース)
* **フロントエンド（画面・UI）**: Access フォーム機能
* **バックエンド（ロジック）**: **VBA (Visual Basic for Applications)** および Access マクロ
* **データストア**: Access ネイティブテーブル

---

## 3. システムの全体構成（解析結果）

このシステムは、非常に本格的な**「在庫管理・販売管理システム（ERPの小規模版）」**です。
構成要素は大きく以下の4つに分かれています。

### ① テーブル (データ構造)

従業員、顧客、商品、注文などの業務データを管理するためのテーブルが多数定義されています。

* `Customers` (顧客) / `Employees` (従業員) / `Suppliers` (仕入先)
* `Products` (商品) / `Inventory Transactions` (在庫トランザクション)
* `Orders`, `Order Details` (注文・受注明細)
* `Purchase Orders`, `Purchase Order Details` (発注・発注明細)
* `Invoices` (請求書)
* `Employee Privileges` (従業員権限)

### ② フォーム (ユーザーインターフェース)

合計34個の画面（フォーム）が実装されており、操作メニューや入力画面として機能しています。

* **メイン画面**: `Home`, `Startup Screen`, `Login Dialog`
* **一覧/詳細画面**: `Customer List`, `Customer Details`, `Employee List`, `Product Details`
* **トランザクション画面**: `Order Details` (受注入力), `Purchase Order Details` (発注入力)
* **分析ダッシュボード**: `Sales Analysis Form`, `Product Category Sales by Month` (グラフ・チャート表示)

### ③ VBAモジュール (ビジネスロジック)

内部には高度な制御を行うVBAコードが多数記述されています。主なモジュールは以下の通りです。

* **Inventory (在庫管理)**: 在庫の引き当てや補充ロジック、在庫ステータスの管理。
* **PurchaseOrders (発注管理)**: 仕入先への発注書作成や承認フロー（`Generate`関数などが存在）。
* **CustomerOrders (顧客注文)**: 受注から請求書（Invoice）作成までの処理。
* **Privileges (権限管理)**: ユーザー（従業員）ごとにシステム操作権限や発注承認権限を制御（例：`CanApprovePurchases` 関数）。
* **ErrorHandling**: システム全体のエラー処理を共通化し、予期せぬエラー時にアプリが落ちないようにする仕組み。

### ④ レポート (帳票・出力)

印刷やPDF出力用の帳票レイアウトが15種類実装されています。

* **売上分析**: `Monthly Sales Report`, `Quarterly Sales Report`, `Yearly Sales Report`
* **取引帳票**: `Invoice` (請求書)
* **台帳・名簿**: `Employee Address Book`, `Customer Phone Book`

---

## 結論

この `.accdb` ファイルは、データの保存場所としてだけでなく、**画面（フォーム）、業務ロジック（VBA/マクロ）、および帳票出力機能を全て一つのファイルに内包した完成された業務アプリケーション** です。

おそらく、Microsoft Accessの強力なテンプレート（「ノースウィンド(Northwind)」などの商取引テンプレートをベースにしているか、それと同等の本格的な構成）を利用して構築された販売・在庫管理システムであると推測されます。
