# ワークスペース再構築手順（NAT Gateway不要・コスト最小化）

## ⚠️ 先に実施していただいた「SGルール追加」について
**無駄ではありません！** むしろ**絶対に必要**な作業でした。
ワークスペースを作り直してクラシッククラスターが起動するようになっても、RDSのポート5432に対する通信許可（Egress）がなければ結局データベースには繋がりません。先ほど追加していただいたルールはそのまま活かされますのでご安心ください。

---

## 段取り（今後のステップ）

以下の手順で Databricks Account Console から環境を再構築します。

### 1. 既存ワークスペースの削除
1. [Databricks Account Console](https://accounts.cloud.databricks.com/) にログイン
2. 左メニュー **Workspaces** を開き、現在の `northwind-workspace` を選択
3. 右上の `Delete`（または `...` メニューから削除）を実行してワークスペースを削除します。

### 2. ネットワーク設定の「再登録」
1. 左メニュー **Cloud resources** → **Network** タブを開きます。
2. 既存の `northwind-network` があれば削除するか、新しく名前を変えて（例: `northwind-network-v2`） **Add network configuration** をクリックします。
3. クラウドフォーメーションの出力を使い、今まで通りVPC・サブネット・SGのIDを入力します。
4. **【重要】** 画面のどこかにある **「Enable secure cluster connectivity (No Public IP)」のチェックを外します**（またはトグルをOFFにします）。
5. 登録（Save）します。

### 3. ワークスペースの再作成
1. **Workspaces** メニューから再度「Create workspace（Custom）」を実行します。
2. 以下を選択します:
   - Credential: 既存の `northwind-credential`
   - Storage: 既存の `northwind-storage`
   - Network: **新しく作った `northwind-network-v2`**
3. ワークスペースを作成します。

### 4. 初期設定のやり直し
新しいワークスペースに入り、実装手順書の以下のフローを再度実施します。

- **Step 2-3**: クラスター `northwind-cluster` の作成（自動でパブリックIPが付き、IGW経由で即起動するはずです）
- **Step 2-4〜2-6**: Storage Credentialの登録、カタログの作成、Secret Scope（RDSのパスワード等）の登録
- **Phase 3**: `00_setup_unity_catalog.py` の実行
- **Phase 4**: [01_load_northwind_to_rds.py](file:///c:/Users/haru/Documents/GitHub/databricks_datamng/AWS%E3%82%B7%E3%83%B3%E3%82%B0%E3%83%AB%E3%82%AF%E3%83%A9%E3%82%A6%E3%83%89Ver/%E9%96%8B%E7%99%BA%E3%83%89%E3%82%AD%E3%83%A5%E3%83%A1%E3%83%B3%E3%83%88/notebooks/01_load_northwind_to_rds.py) の実行（ここで接続成功するはずです！）

---

> ※この一連の作業が終われば、NAT Gateway費用は一切かからず、完全なコスト最適化状態で学習を進められます。
> ※『実装手順書.md』には、今後同じ間違いが起きないよう「チェックを必ず外すこと」を追記しておきました。
