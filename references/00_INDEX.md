# rippuGUI 参考文献インデックス

このフォルダは、調教型ヒューマノイド「瞳」の **会話AI＋GUIプロトタイプ** を作るための参考文献置き場です。
本体ハード（体温・表情アクチュエータ等）より先に、**画面上で会話・状態変化・ユーザーごとの差分**を試す段階向け。

## 読む順番（おすすめ）

1. `01_project-brief.md` … 何を作るか（プロダクト定義）
2. `architecture/02_conversation-stack.md` … 会話プロトタイプの推奨構成
3. `architecture/03_training-state-and-memory.md` … 「調教で反応が変わる」の実装の芯
4. `gui-prototype/04_gui-mvp.md` … まず作るGUIの最小機能
5. `opensource/05_related-projects.md` … 真似しやすいOSS
6. `papers/06_academic-and-systems.md` … 論文・システム事例

## ローカル環境との接続（MSI）

- チャットLLM: 既存 Ollama + `Qwen3-8B-JP-Uncensored`（`E:\LocalAI`）
- UI案: Python（Gradio / FastAPI+Web）またはデスクトップGUI
- 後で実機に挿す想定の口: 「発話」「表情パラメータ」「親密度/調教ステート」をAPI化

