from engine import ChatEngine, ChatError

try:
    engine = ChatEngine.from_project()
    result = engine.chat([{"role": "user", "content": "こんにちは。一言だけ返事して。"}], retries=1)
    print("OK")
    print(result.content[:500])
except ChatError as e:
    print("ERR", e)
