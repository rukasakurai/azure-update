# Azure Update Deck

このプロジェクトは、Azureの更新情報を取得して処理し、PowerPoint形式のプレゼンテーションデッキを生成する2つのPythonスクリプトで構成されています。

## 前提条件

- Python 3.7以上
- pip (Pythonパッケージインストーラー)
- Azure CLI（`az` コマンド。`az login` によるEntra ID認証に必要）
- Microsoft Foundry リソースとモデルデプロイ

## セットアップ

1. リポジトリをクローンします:
    ```sh
    git clone https://github.com/shyamagu/azure-update.git
    cd azure-update
    ```

2. 仮想環境を作成してアクティブにします:
    ```sh
    python -m venv venv
    source venv/bin/activate  # Windowsの場合は `venv\Scripts\activate`
    ```

3. 必要なパッケージをインストールします:
    ```sh
    pip install -r requirements.txt
    ```

4. プロジェクトのルートディレクトリに `.env` ファイルを作成し、Microsoft Foundryの設定を追加します:
    ```env
    AZURE_OPENAI_ENDPOINT=your_foundry_endpoint
    MODEL_DEPLOYMENT_NAME=your_model_deployment
    ```
    `AZURE_OPENAI_ENDPOINT` は既存コードとの互換性のための環境変数名です。値には Microsoft Foundry のエンドポイントを指定します。

5. 認証はEntra ID（キーレス）を使用します。`DefaultAzureCredential` でトークンを取得するため、事前にサインインしてください:
    ```sh
    az login
    ```
    サインインするIDには、対象のMicrosoft Foundryリソースでモデルを呼び出すための権限が必要です。

## 使用方法

### ステップ1: Azure更新情報の取得

`1_get_azure_update.py` スクリプトを実行して最新のAzure更新情報を取得します。日付を `YYYY-MM-DD` 形式で引数として指定する必要があります。
指定された日付**以降**の更新情報を取得しています。

```sh
python 1_get_azure_update.py 2025-01-01
```

このコマンドは、更新情報を含むMarkdownファイルを作成します。タイトルの区分には `一般提供`、`パブリックプレビュー`、`プライベートプレビュー`、`開発中`、`リタイアメント` を使用します。

### ステップ2: ステータスの確認（必要な場合）

取得元のタイトル、APIステータス、提供段階が一致しない場合、Markdownには `<!-- status-review` コメントと `要確認` 区分が追加されます。

このリポジトリの `azure-update-powerpoint` Agent Skill を利用すると、既存の参考リンクと公式Microsoftドキュメントを調査し、`一般提供`、`パブリックプレビュー`、`プライベートプレビュー`、`開発中`、`リタイアメント`、または `その他の更新` に更新できます。該当コメントがなければ、このステップは不要です。

### ステップ3: プレゼンテーションデッキの生成

`2_make_jp_update_pptx.py` スクリプトを実行して、取得した更新情報をMicrosoft Foundryのモデルで処理し、PowerPoint形式のプレゼンテーションデッキを生成します。タイトル本文のみを翻訳し、Markdownで確定した区分はそのまま使用します。

```sh
python 2_make_jp_update_pptx.py
```

デフォルトでは、最新の `azure_update*.md` ファイルを使用します。特定のファイルを指定することもできます:

```sh
python 2_make_jp_update_pptx.py azure_update_20250101_20250122.md
```

出力は `pptx_azure_update_*.pptx` ファイルとなります。

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。