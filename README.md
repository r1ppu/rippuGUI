# Rippu Avatar Lab

GUIでタッチや表情へのアバター反応を検証するMVPです。対話コアはGUIから分離されており、将来はカメラ、触覚センサー、ロボットのアクチュエータへアダプターを置き換えられます。

## 起動

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

画面のアバターをクリックすると、頭、顔、胸、手の位置に応じた反応を確認できます。表情の選択欄はカメラ認識の代替入力です。

## VRoid / VRMアバター

公式VRMサンプルの `Seed-san` をデフォルトモデルとして同梱しています。著作者はVirtualCast, Inc.、ライセンスは [VRM Public License 1.0](https://vrm.dev/en/licenses/1.0/index) です。詳しい出典は [assets/Seed-san-LICENSE.md](assets/Seed-san-LICENSE.md) を確認してください。

画面の `VRMを読み込む` ボタンから、別の利用許諾済み `.vrm` ファイルにも差し替えられます。Qt WebEngine上でthree-vrmを使って表示し、表情反応をVRMの表情へ渡します。

## 会話AI

GitHub側の会話エンジンをPySide6 GUIへ統合しています。画面下部の「めあとの会話」から、Cloudflare Accessで保護されたOpenAI互換APIへ会話履歴を送信できます。初回利用時に設定ファイルを作成してください。

```powershell
Copy-Item config\settings.example.json config\settings.json
# config\settings.json に Cloudflare Access の Client ID / Secret を設定
\.venv\Scripts\python.exe run.py
```

`config/settings.json` は秘密情報を含むためGit管理対象外です。会話AIが利用できない場合も、VRM表示、ルールベース反応、イベントログは利用できます。

VRMのタッチ判定は、頭、額、左右の目、左右の頬、口、首、左右の肩、胸、腹部、左右の上腕、左右の手、左右の太もも、左右の足の20領域です。

VRM表示には初回起動時にthree.jsとthree-vrmをCDNから読み込みます。オフライン環境ではモデル表示は利用できませんが、対話コアとログは引き続きテストできます。

## Ollama

Ollamaを起動し、利用するモデルを取得してからアプリを起動します。

```powershell
ollama pull gemma3
\.venv\Scripts\python.exe run.py
```

接続先とモデルは環境変数で変更できます。

```powershell
$env:OLLAMA_HOST = "http://localhost:11434"
$env:OLLAMA_MODEL = "gemma3"
\.venv\Scripts\python.exe run.py
```

Ollamaが停止していても、ルールベースの反応とイベントログは利用できます。LLM通信はGUIスレッドと分離され、応答待ちで画面が固まらない構成です。

イベント反応でOllamaを使う場合だけ、起動前に `$env:OLLAMA_ENABLED = "1"` を設定してください。会話欄のAIはGitHub側のリモート会話APIを使用します。

## テスト

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

`app/domain.py` はPySide6やOllamaに依存しないため、実機移植時にも対話ロジックを再利用できます。