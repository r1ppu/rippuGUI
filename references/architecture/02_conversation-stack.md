# 02 会話スタック（プロトタイプ推奨）

## ねらい
画面だけの「瞳」で、調教・記憶・反応変化を実験できる最小構成。

## 推奨レイヤ

```
[GUI]
  チャット / 調教スライダー / ステータス表示 / ログ
    ↓ events (user_message, tease, intimacy, praise, scold...)
[Agent Runtime]
  system prompt（瞳の人格）
  + 現在ステート（affection, obedience, arousal, trust...）
  + メモリ検索結果（このユーザーの過去）
    ↓
[LLM]  ローカル Ollama（例: Qwen3-JP-Uncensored）
    ↓
[Memory Store]
  セッション履歴 / エピソード要約 / ユーザープロファイル
```

## 参考になる既存設計パターン
- **ReAct + tools**: 記憶検索・ステート更新をツール呼び出しにする
- **RAG memory**: ユーザー別の長期記憶をチャンクで保存し、関連のみ注入
- **Affective loop**: 感情・ムードが次の発話トーンを変える
- **Embodied later**: いまはGUIイベント、後で「接触」「視線」センサーに差し替え

## MSI 上での現実的な初期実装
- Backend: FastAPI または Gradio
- LLM: `http://127.0.0.1:11434`（既存 Ollama）
- DB: SQLite（ユーザーID、ステート、メッセージ、要約）
- Prompt: 「瞳」の口調・禁忌（成人同意・安全ワード）・ステート反映ルールを明示

