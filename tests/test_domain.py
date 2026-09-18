from app.domain import InteractionEngine, InteractionEvent


def test_head_touch_is_happy():
    engine = InteractionEngine()
    reaction = engine.handle(InteractionEvent("touch", "test", "touch", "head", 0.3))
    assert reaction.emotion == "happy"
    assert engine.state.trust > 0.5


def test_strong_touch_is_uncomfortable():
    reaction = InteractionEngine().handle(InteractionEvent("touch", "test", "touch", "head", 0.9))
    assert reaction.emotion == "uncomfortable"


def test_speech_becomes_listening_reaction():
    reaction = InteractionEngine().handle(InteractionEvent("speech", "test", "こんにちは"))
    assert "こんにちは" in reaction.message
    assert reaction.actions[0].name == "listen"
