# rippuGUI

調教型ヒューマノイド「瞳」系の **会話AI GUI プロトタイプ**（プロジェクト名 R1ppu）。

裏の会話エンジンと仮置きGUIを分けています。本GUIは後から差し替え前提です。

## いま動くもの
- `engine/` … Cloudflare Access + llama.cpp（`llamacpp.meameme.win`）へ話す会話エンジン
- `app.py` … 仮置きGUI（Gradio）
- `config/settings.example.json` … 設定テンプレ（Secretなし）
- `config/system_prompt.txt` … 健全設定のみのめあちゃん会話プロンプト
- `config/settings.json` … ローカル用実設定（**gitignore。絶対にコミットしない**）

## セットアップ

```powershell
cd E:\projects\rippuGUI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy config\settings.example.json config\settings.json
# settings.json に Cloudflare Access の Client ID / Secret を入れる
```

## 起動

```powershell
cd E:\projects\rippuGUI
.\.venv\Scripts\Activate.ps1
python app.py
```

ブラウザ: http://127.0.0.1:7860

## ドキュメント
- 参考資料: [`references/00_INDEX.md`](references/00_INDEX.md)
- プロダクト概要: [`references/01_project-brief.md`](references/01_project-brief.md)

## 注意
- `config/settings.json` にはシークレットが入るため push 禁止
- MSIローカル Ollama は主経路に使わない（設計確定済み）
