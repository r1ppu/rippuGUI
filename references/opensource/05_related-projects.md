# 05 関連オープンソース・プロダクト（実装の参考）

## 会話・エージェント
- **Ollama** — ローカルLLM実行（本機導入済み）  
  https://ollama.com
- **Open WebUI** — 汎用チャットUI（参考。瞳専用GUIの代替にはしない）  
  https://github.com/open-webui/open-webui
- **LangGraph / LlamaIndex** — ステートフルエージェント・記憶配線  
  https://github.com/langchain-ai/langgraph  
  https://github.com/run-llama/llama_index
- **SillyTavern** — キャラ会話UI・ワールドインフォ・ステート系の先行事例（成人向けコミュニティで多用）  
  https://github.com/SillyTavern/SillyTavern

## ソーシャルロボット / エンボディド
- **Nadine social robot (LLM + memory + affect)** — 構成の参考論文あり  
  https://arxiv.org/abs/2405.20189
- **Ludi 0.1** — ヒューマノイド上のエージェント構成の最近例  
  https://arxiv.org/html/2608.22035

## GUIプロトタイプ向き
- Gradio: https://www.gradio.app
- FastAPI: https://fastapi.tiangolo.com
- NiceGUI（Pythonデスクトップ寄り）: https://nicegui.io

## 使い方の指針
- 「キャラ一貫＋長期記憶」は SillyTavern / Nadine を観察
- 「調教ステート」は自前の数値ステートで制御（完全にLLM任せにしない）
- 「実機」は後から event bus にセンサーを繋ぐ前提でGUIボタンを置く

