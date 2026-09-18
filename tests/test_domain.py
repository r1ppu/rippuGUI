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


def test_touch_event_resolution_uses_body_location():
    from app.domain import TouchEvent, resolve_touch_reaction

    touch = TouchEvent("left_eye", source="vr", intensity=0.5, confidence=0.9)
    reaction = resolve_touch_reaction(touch)

    assert reaction.emotion == "surprised"
    assert "目" in reaction.message


def test_touch_event_resolution_supports_pointer_and_vr_sources():
    from app.domain import TouchEvent, resolve_touch_reaction

    vr_reaction = resolve_touch_reaction(TouchEvent("chest", source="vr", intensity=0.7, confidence=0.8))
    pointer_reaction = resolve_touch_reaction(TouchEvent("right_hand", source="pointer", intensity=0.6, confidence=0.7))

    assert vr_reaction.emotion == "happy"
    assert pointer_reaction.emotion == "happy"


def test_touch_message_mentions_the_body_part_name():
    from app.domain import TouchEvent, resolve_touch_reaction

    reaction = resolve_touch_reaction(TouchEvent("left_eye", source="vr", intensity=0.4, confidence=0.9))

    assert "左目" in reaction.message
    assert "触った" in reaction.message


def test_touch_message_uses_the_same_location_name_as_the_touched_area():
    from app.domain import TouchEvent, resolve_touch_reaction

    reaction = resolve_touch_reaction(TouchEvent("left_upper_arm", source="gui", intensity=0.3, confidence=0.9))

    assert "左上腕" in reaction.message
    assert "左肩" not in reaction.message


def test_ambiguous_ui_locations_are_normalized_to_canonical_parts():
    from app.domain import normalize_location

    assert normalize_location("face") == "forehead"
    assert normalize_location("hand") == "left_hand"


def test_engine_normalizes_touch_locations_before_recording_state():
    from app.domain import InteractionEngine, InteractionEvent

    engine = InteractionEngine()
    reaction = engine.handle(InteractionEvent("touch", "gui", "touch", "face", 0.4))

    assert reaction.message.startswith("額")
    assert engine.state.last_event is not None
    assert engine.state.last_event.location == "forehead"
