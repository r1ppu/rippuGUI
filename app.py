"""R1ppu placeholder GUI. Uses ChatEngine; replaceable by real GUI later."""
from __future__ import annotations

from pathlib import Path

import gradio as gr

from engine import ChatEngine, ChatError

ROOT = Path(__file__).resolve().parent


def build_engine() -> ChatEngine:
    return ChatEngine.from_project(ROOT)


def respond(message: str, history: list[dict[str, str]]):
    message = (message or "").strip()
    if not message:
        yield history
        return

    history = list(history or [])
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": "生成中…"})
    yield history

    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in history[:-1]
        if m.get("role") in ("user", "assistant") and m.get("content") != "生成中…"
    ]

    try:
        engine = build_engine()
        result = engine.chat(messages, retries=1)
        history[-1] = {"role": "assistant", "content": result.content}
    except ChatError as e:
        history[-1] = {"role": "assistant", "content": f"エラー: {e}"}
    except Exception:
        history[-1] = {"role": "assistant", "content": "エラー: 予期しない障害が起きました。"}
    yield history


def clear():
    return []


def main() -> None:
    with gr.Blocks(title="R1ppu 仮置きGUI") as demo:
        gr.Markdown("## R1ppu 仮置きGUI\n裏の会話エンジンを試す画面です。本GUI差し替え前提。")
        chatbot = gr.Chatbot(label="会話", height=480, type="messages")
        with gr.Row():
            txt = gr.Textbox(label="メッセージ", placeholder="ここに入力", scale=4)
            send = gr.Button("送信", variant="primary", scale=1)
        clear_btn = gr.Button("クリア")

        send.click(respond, inputs=[txt, chatbot], outputs=chatbot).then(lambda: "", None, txt)
        txt.submit(respond, inputs=[txt, chatbot], outputs=chatbot).then(lambda: "", None, txt)
        clear_btn.click(clear, outputs=chatbot)

    demo.queue().launch(server_name="127.0.0.1", server_port=7860, inbrowser=False)


if __name__ == "__main__":
    main()
