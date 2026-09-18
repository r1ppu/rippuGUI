"""Ollama adapter with a deterministic fallback."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .domain import AvatarState, InteractionEvent, LlmReactionProposal, Emotion


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma3", timeout: float = 15.0) -> None:
        self.url = base_url.rstrip("/") + "/api/chat"
        self.model = model
        self.timeout = timeout

    def propose(self, state: AvatarState, event: InteractionEvent) -> LlmReactionProposal:
        prompt = {
            "state": {"emotion": state.emotion, "trust": round(state.trust, 2), "energy": round(state.energy, 2)},
            "event": {"type": event.type, "value": event.value, "location": event.location, "intensity": event.intensity},
            "instruction": "短い自然な日本語で返答し、JSONだけを返してください。emotionはneutral,happy,sad,surprised,uncomfortableのいずれか。animationはsmile,blink,concerned,wide_eyes,calm,listenのいずれか。",
        }
        body = json.dumps({
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": "あなたは安全な対話アバターです。"},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
        }).encode("utf-8")
        request = urllib.request.Request(self.url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        result = json.loads(payload["message"]["content"])
        emotion: Emotion = result.get("emotion", "neutral")
        if emotion not in {"neutral", "happy", "sad", "surprised", "uncomfortable"}:
            emotion = "neutral"
        return LlmReactionProposal(str(result.get("reply", "認識しました。")), emotion, str(result.get("animation", "blink")))


__all__ = ["OllamaClient"]
