"""R1ppu conversation engine: calls remote llama.cpp via Cloudflare Access."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ChatError(Exception):
    """User-facing engine failure."""


@dataclass
class ChatResult:
    content: str
    reasoning: str
    raw: dict[str, Any]


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
                "設定ファイルが見つかりません。config/settings.example.json をコピーして "
                "config/settings.json を作ってください。"
            )
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        prompt_path = root / "config" / "system_prompt.txt"
        system_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
        missing = [
            k
            for k in ("base_url", "model", "cf_access_client_id", "cf_access_client_secret")
            if not str(settings.get(k, "")).strip()
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
            "User-Agent": "r1ppu-engine/0.1",
        }

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.base_url + path
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        method = "GET" if payload is None else "POST"
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                raw = resp.read()
                ctype = resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:300]
            if e.code in (401, 403) or "Cloudflare Access" in body or "Sign in" in body:
                raise ChatError("認証に失敗しました。Service Token を確認してください。") from e
            if e.code == 429:
                raise ChatError("サーバが混雑しています。少し待って再試行してください。") from e
            raise ChatError(f"サーバエラーです（HTTP {e.code}）。") from e
        except urllib.error.URLError as e:
            raise ChatError("接続できませんでした。ネットワークかサーバ起動を確認してください。") from e
        except TimeoutError as e:
            raise ChatError("応答がタイムアウトしました。") from e

        text = raw.decode("utf-8", errors="replace")
        if "text/html" in ctype or text.lstrip().lower().startswith("<!doctype"):
            raise ChatError("認証に失敗しました。Service Token または Access 設定を確認してください。")
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ChatError("サーバから予期しない応答が返りました。") from e

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

        last_error: Exception | None = None
        attempts = max(1, retries + 1)
        for i in range(attempts):
            try:
                data = self._request("/v1/chat/completions", payload)
                return self._parse_result(data)
            except ChatError as e:
                last_error = e
                if i >= attempts - 1:
                    break
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
        if isinstance(reasoning, str):
            reasoning = reasoning.strip()
        else:
            reasoning = str(reasoning)

        display = content
        if self.thinking_mode == "content_first" and not display:
            if reasoning:
                display = "（思考中の出力のみ）\n" + reasoning
            else:
                display = "（空の応答）"
        elif self.thinking_mode == "include_reasoning" and reasoning:
            display = (content + "\n\n---\n" + reasoning).strip() if content else reasoning

        return ChatResult(content=display, reasoning=reasoning, raw=data)
