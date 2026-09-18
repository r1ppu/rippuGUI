"""Framework-independent interaction domain."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Literal

Emotion = Literal["neutral", "happy", "sad", "surprised", "uncomfortable"]

BODY_PARTS: dict[str, dict[str, str]] = {
    "head": {"label": "頭", "group": "head"},
    "forehead": {"label": "額", "group": "face"},
    "left_eye": {"label": "左目", "group": "face"},
    "right_eye": {"label": "右目", "group": "face"},
    "left_cheek": {"label": "左頬", "group": "face"},
    "right_cheek": {"label": "右頬", "group": "face"},
    "mouth": {"label": "口", "group": "face"},
    "neck": {"label": "首", "group": "upper_body"},
    "left_shoulder": {"label": "左肩", "group": "upper_body"},
    "right_shoulder": {"label": "右肩", "group": "upper_body"},
    "left_upper_arm": {"label": "左上腕", "group": "upper_body"},
    "right_upper_arm": {"label": "右上腕", "group": "upper_body"},
    "chest": {"label": "胸", "group": "upper_body"},
    "stomach": {"label": "腹", "group": "upper_body"},
    "left_hand": {"label": "左手", "group": "arm"},
    "right_hand": {"label": "右手", "group": "arm"},
    "left_thigh": {"label": "左太もも", "group": "lower_body"},
    "right_thigh": {"label": "右太もも", "group": "lower_body"},
    "left_foot": {"label": "左足", "group": "lower_body"},
    "right_foot": {"label": "右足", "group": "lower_body"},
}

LOCATION_ALIASES = {
    "left_upper_arm": "left_upper_arm",
    "right_upper_arm": "right_upper_arm",
    "leftarm": "left_upper_arm",
    "rightarm": "right_upper_arm",
    "left_arm": "left_upper_arm",
    "right_arm": "right_upper_arm",
    "leftshoulder": "left_shoulder",
    "rightshoulder": "right_shoulder",
    "left_shoulder": "left_shoulder",
    "right_shoulder": "right_shoulder",
    "left_hand": "left_hand",
    "right_hand": "right_hand",
    "hand_left": "left_hand",
    "hand_right": "right_hand",
    "hand": "left_hand",
    "face": "forehead",
    "body": "chest",
    "left_eye": "left_eye",
    "right_eye": "right_eye",
    "eye_left": "left_eye",
    "eye_right": "right_eye",
    "left_cheek": "left_cheek",
    "right_cheek": "right_cheek",
    "cheek_left": "left_cheek",
    "cheek_right": "right_cheek",
}


TOUCH_REACTIONS: dict[str, dict[str, object]] = {
    "head": {"emotion": "happy", "message": "頭を触ってくれたのね。ありがとう。", "animation": "smile", "trust_delta": 0.02},
    "forehead": {"emotion": "happy", "message": "額を触ったのね。やさしい気持ちが伝わるわ。", "animation": "smile", "trust_delta": 0.01},
    "left_eye": {"emotion": "surprised", "message": "左目を触ったのね。びっくりしちゃったわ。", "animation": "blink", "trust_delta": 0.0},
    "right_eye": {"emotion": "surprised", "message": "右目を触ったのね。びっくりしちゃったわ。", "animation": "blink", "trust_delta": 0.0},
    "left_cheek": {"emotion": "happy", "message": "左頬を触ったのね。ほっとするわ。", "animation": "smile", "trust_delta": 0.01},
    "right_cheek": {"emotion": "happy", "message": "右頬を触ったのね。ほっとするわ。", "animation": "smile", "trust_delta": 0.01},
    "mouth": {"emotion": "surprised", "message": "口元を触ったのね。少しドキッとしたわ。", "animation": "blink", "trust_delta": 0.0},
    "neck": {"emotion": "surprised", "message": "首に触れたのね。少し照れちゃうわ。", "animation": "look_down", "trust_delta": 0.0},
    "left_shoulder": {"emotion": "neutral", "message": "左肩を触ったのね。落ち着く感じがするわ。", "animation": "look_down", "trust_delta": 0.005},
    "right_shoulder": {"emotion": "neutral", "message": "右肩を触ったのね。落ち着く感じがするわ。", "animation": "look_down", "trust_delta": 0.005},
    "left_upper_arm": {"emotion": "neutral", "message": "左上腕を触ったのね。落ち着く感じがするわ。", "animation": "look_down", "trust_delta": 0.005},
    "right_upper_arm": {"emotion": "neutral", "message": "右上腕を触ったのね。落ち着く感じがするわ。", "animation": "look_down", "trust_delta": 0.005},
    "chest": {"emotion": "happy", "message": "胸を触ったのね。ちょっと嬉しいわ。", "animation": "smile", "trust_delta": 0.01},
    "stomach": {"emotion": "surprised", "message": "お腹を触ったのね。びっくりしたわ。", "animation": "look_down", "trust_delta": 0.0},
    "left_hand": {"emotion": "happy", "message": "左手を触ったのね。手を握りたい気持ちが伝わるわ。", "animation": "smile", "trust_delta": 0.015},
    "right_hand": {"emotion": "happy", "message": "右手を触ったのね。手を握りたい気持ちが伝わるわ。", "animation": "smile", "trust_delta": 0.015},
    "left_thigh": {"emotion": "surprised", "message": "左太ももを触ったのね。少し驚いたわ。", "animation": "look_down", "trust_delta": 0.0},
    "right_thigh": {"emotion": "surprised", "message": "右太ももを触ったのね。少し驚いたわ。", "animation": "look_down", "trust_delta": 0.0},
    "left_foot": {"emotion": "neutral", "message": "左足を触ったのね。足元に気を使ってくれてる感じがするわ。", "animation": "look_down", "trust_delta": 0.0},
    "right_foot": {"emotion": "neutral", "message": "右足を触ったのね。足元に気を使ってくれてる感じがするわ。", "animation": "look_down", "trust_delta": 0.0},
    "default": {"emotion": "neutral", "message": "そこを触ったのね。反応してみるわ。", "animation": "look_down", "trust_delta": 0.0},
}



@dataclass(frozen=True)
class TouchEvent:
    location: str
    source: str = "pointer"
    intensity: float = 1.0
    confidence: float = 1.0
    x: float | None = None
    y: float | None = None
    z: float | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


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


def normalize_location(location: str) -> str:
    token = location.strip().lower().replace(" ", "_")
    return LOCATION_ALIASES.get(token, token)


def resolve_touch_reaction(touch: TouchEvent) -> Reaction:
    normalized = normalize_location(touch.location)
    if touch.intensity >= 0.85:
        return Reaction("uncomfortable", "少し強いです。", (ActionCommand("animation", "step_back", 700),), -0.03)

    template = TOUCH_REACTIONS.get(normalized, TOUCH_REACTIONS["default"])
    emotion = template["emotion"]
    message = template["message"]
    animation = template["animation"]
    trust_delta = float(template.get("trust_delta", 0.0))

    return Reaction(
        str(emotion),
        str(message),
        (ActionCommand("animation", str(animation), 900),),
        trust_delta,
    )


class InteractionEngine:
    """Deterministic reactions that also work without Ollama."""

    def __init__(self) -> None:
        self.state = AvatarState()

    def handle(self, event: InteractionEvent) -> Reaction:
        normalized_event = event
        if event.type == "touch" and event.location:
            normalized_event = replace(event, location=normalize_location(event.location))

        reaction = self._react(normalized_event)
        self.state.apply(reaction, normalized_event)
        return reaction

    def _react(self, event: InteractionEvent) -> Reaction:
        if event.type == "touch":
            touch = TouchEvent(
                location=(event.location or event.value or "body"),
                source=event.source,
                intensity=event.intensity,
                confidence=event.confidence,
            )
            return resolve_touch_reaction(touch)

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