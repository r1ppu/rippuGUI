"""Framework-independent interaction domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

Emotion = Literal["neutral", "happy", "sad", "surprised", "uncomfortable"]


@dataclass(frozen=True)
class InteractionEvent:
    type: Literal["touch", "expression", "speech"]
    source: str
    value: str
    location: str | None = None
    intensity: float = 1.0
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class ActionCommand:
    type: Literal["animation", "speech"]
    name: str
    duration_ms: int = 0


@dataclass(frozen=True)
class Reaction:
    emotion: Emotion
    message: str
    actions: tuple[ActionCommand, ...] = ()
    trust_delta: float = 0.0


@dataclass
class AvatarState:
    emotion: Emotion = "neutral"
    trust: float = 0.5
    energy: float = 0.8
    last_event: InteractionEvent | None = None

    def apply(self, reaction: Reaction, event: InteractionEvent) -> None:
        self.emotion = reaction.emotion
        self.trust = max(0.0, min(1.0, self.trust + reaction.trust_delta))
        self.energy = max(0.0, self.energy - 0.01)
        self.last_event = event


class InteractionEngine:
    """Deterministic reactions that also work without Ollama."""

    def __init__(self) -> None:
        self.state = AvatarState()

    def handle(self, event: InteractionEvent) -> Reaction:
        reaction = self._react(event)
        self.state.apply(reaction, event)
        return reaction

    def _react(self, event: InteractionEvent) -> Reaction:
        if event.type == "touch":
            if event.intensity >= 0.85:
                return Reaction("uncomfortable", "少し強いです。", (ActionCommand("animation", "step_back", 700),), -0.03)
            if event.location == "head":
                return Reaction("happy", "ありがとう。", (ActionCommand("animation", "smile", 1200),), 0.02)
            if event.location in {"forehead", "left_cheek", "right_cheek"}:
                return Reaction("happy", "やさしく触れてくれましたね。", (ActionCommand("animation", "smile", 900),), 0.01)
            if event.location in {"left_eye", "right_eye"}:
                return Reaction("surprised", "目の近くですね。", (ActionCommand("animation", "blink", 500),), 0.0)
            if event.location == "mouth":
                return Reaction("surprised", "口の近くですね。", (ActionCommand("animation", "blink", 500),), 0.0)
            if event.location == "neck":
                return Reaction("surprised", "首に触れましたね。", (ActionCommand("animation", "look_down", 700),), 0.0)
            if event.location in {"left_shoulder", "right_shoulder", "left_upper_arm", "right_upper_arm"}:
                return Reaction("neutral", "腕に触れましたね。", (ActionCommand("animation", "look_down", 700),), 0.005)
            if event.location == "chest":
                return Reaction("happy", "ここに触れましたね。", (ActionCommand("animation", "look_down", 800),), 0.01)
            if event.location == "stomach":
                return Reaction("surprised", "お腹に触れましたね。", (ActionCommand("animation", "look_down", 800),), 0.0)
            if event.location in {"left_hand", "right_hand"}:
                return Reaction("happy", "手を握りますか？", (ActionCommand("animation", "smile", 800),), 0.015)
            if event.location in {"left_thigh", "right_thigh"}:
                return Reaction("surprised", "足に触れましたね。", (ActionCommand("animation", "look_down", 800),), 0.0)
            if event.location in {"left_foot", "right_foot"}:
                return Reaction("neutral", "足元に触れましたね。", (ActionCommand("animation", "look_down", 800),), 0.0)
            return Reaction("neutral", "そこに触れましたね。")

        if event.type == "expression":
            reactions: dict[str, tuple[Emotion, str, str]] = {
                "happy": ("happy", "うれしそうですね。", "smile"),
                "sad": ("sad", "少し心配です。", "concerned"),
                "surprised": ("surprised", "驚きましたか？", "wide_eyes"),
                "angry": ("uncomfortable", "落ち着いて話しましょう。", "calm"),
            }
            emotion, message, animation = reactions.get(event.value, ("neutral", "表情を見ています。", "blink"))
            return Reaction(emotion, message, (ActionCommand("animation", animation, 900),))

        if event.type == "speech":
            return Reaction(self.state.emotion, f"「{event.value}」と聞きました。", (ActionCommand("animation", "listen", 600),))

        return Reaction("neutral", "認識しました。")


@dataclass(frozen=True)
class LlmReactionProposal:
    reply: str
    emotion: Emotion
    animation: str


def proposal_to_reaction(proposal: LlmReactionProposal) -> Reaction:
    allowed_animations = {"smile", "blink", "concerned", "wide_eyes", "calm", "listen"}
    animation = proposal.animation if proposal.animation in allowed_animations else "blink"
    return Reaction(
        proposal.emotion,
        proposal.reply,
        (ActionCommand("animation", animation, 900),),
    )