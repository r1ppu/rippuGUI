"""Conversation client for the remote OpenAI-compatible API."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ChatError(Exception):
    """User-facing conversation failure."""


@dataclass
class ChatResult:
    content: str
    reasoning: str
    raw: dict[str, Any]
    emotion: str = "neutral"


class ChatEngine:
    def __init__(self, settings: dict[str, Any], system_prompt: str = "") -> None:
        self.base_url = settings["base_url"].rstrip("/")
        self.model = settings["model"]
        self.client_id = settings["cf_access_client_id"]
        self.client_secret = settings["cf_access_client_secret"]
        self.temperature = float(settings.get("temperature", 0.7))
        self.max_tokens = int(settings.get("max_tokens", 512))
        self.thinking_mode = settings.get("thinking_display_mode", "content_first")
        self.timeout_sec = float(settings.get("timeout_sec", 120))
        self.system_prompt = system_prompt.strip()

    @classmethod
    def from_project(cls, project_root: Path | None = None) -> "ChatEngine":
        root = project_root or Path(__file__).resolve().parent.parent
        settings_path = root / "config" / "settings.json"
        if not settings_path.exists():
            raise ChatError(
                "設定ファイルがありません。config/settings.example.json をコピーして "
                "config/settings.json を作成してください。"
            )
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ChatError("設定ファイルを読み込めませんでした。") from exc
        prompt_path = root / "config" / "system_prompt.txt"
        try:
            system_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
        except OSError as exc:
            raise ChatError("システムプロンプトを読み込めませんでした。") from exc
        missing = [
            key
            for key in ("base_url", "model", "cf_access_client_id", "cf_access_client_secret")
            if not str(settings.get(key, "")).strip() or str(settings.get(key)) == "REPLACE_ME"
        ]
        if missing:
            raise ChatError("設定が不足しています: " + ", ".join(missing))
        return cls(settings, system_prompt=system_prompt)

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "CF-Access-Client-Id": self.client_id,
            "CF-Access-Client-Secret": self.client_secret,
            "User-Agent": "r1ppu-avatar-lab/0.1",
        }

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self.base_url + "/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                raw = response.read()
                content_type = response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:300]
            if exc.code in (401, 403) or "Cloudflare Access" in body or "Sign in" in body:
                raise ChatError("認証に失敗しました。Service Tokenを確認してください。") from exc
            if exc.code == 429:
                raise ChatError("サーバが混雑しています。少し待って再試行してください。") from exc
            raise ChatError(f"サーバエラーです（HTTP {exc.code}）。") from exc
        except urllib.error.URLError as exc:
            raise ChatError("接続できませんでした。ネットワークかサーバを確認してください。") from exc
        except TimeoutError as exc:
            raise ChatError("応答がタイムアウトしました。") from exc

        text = raw.decode("utf-8", errors="replace")
        if "text/html" in content_type or text.lstrip().lower().startswith("<!doctype"):
            raise ChatError("認証に失敗しました。Service TokenまたはAccess設定を確認してください。")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ChatError("サーバから予期しない応答が返りました。") from exc

    def chat(self, messages: list[dict[str, str]], retries: int = 1) -> ChatResult:
        api_messages: list[dict[str, str]] = []
        if self.system_prompt:
            api_messages.append({"role": "system", "content": self.system_prompt})
        api_messages.extend(messages)
        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        last_error: ChatError | None = None
        for attempt in range(max(1, retries + 1)):
            try:
                return self._parse_result(self._request(payload))
            except ChatError as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(1.0)
        assert last_error is not None
        raise last_error

    def _parse_result(self, data: dict[str, Any]) -> ChatResult:
        choices = data.get("choices") or []
        if not choices:
            raise ChatError("モデルから返事がありませんでした。")
        message = choices[0].get("message") or {}
        content = (message.get("content") or "").strip()
        reasoning = message.get("reasoning_content") or message.get("reasoning") or ""
        reasoning = reasoning.strip() if isinstance(reasoning, str) else str(reasoning)
        if self.thinking_mode == "content_first" and not content:
            content = "（思考中の出力のみ）\n" + reasoning if reasoning else "（空の応答）"
        elif self.thinking_mode == "include_reasoning" and reasoning:
            content = (content + "\n\n---\n" + reasoning).strip() if content else reasoning
        emotion = "neutral"
        match = re.search(r"\[\[emotion:(neutral|happy|sad|surprised|uncomfortable)\]\]", content, re.IGNORECASE)
        if match:
            emotion = match.group(1).lower()
            content = re.sub(r"\s*\[\[emotion:(?:neutral|happy|sad|surprised|uncomfortable)\]\]", "", content, flags=re.IGNORECASE).strip()
        return ChatResult(content=content, reasoning=reasoning, raw=data, emotion=emotion)
