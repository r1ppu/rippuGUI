from engine import ChatEngine


def test_chat_engine_parses_openai_response():
    engine = ChatEngine(
        {
            "base_url": "https://example.test",
            "model": "test-model",
            "cf_access_client_id": "id",
            "cf_access_client_secret": "secret",
        }
    )

    result = engine._parse_result(
        {"choices": [{"message": {"content": "こんばんは", "reasoning_content": "考えました"}}]}
    )

    assert result.content == "こんばんは"
    assert result.reasoning == "考えました"


def test_chat_engine_extracts_emotion_tag():
    engine = ChatEngine(
        {
            "base_url": "https://example.test",
            "model": "test-model",
            "cf_access_client_id": "id",
            "cf_access_client_secret": "secret",
        }
    )

    result = engine._parse_result({"choices": [{"message": {"content": "うれしいです [[emotion:happy]]"}}]})

    assert result.content == "うれしいです"
    assert result.emotion == "happy"