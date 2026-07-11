from core.config import ProjectConfig
from core.providers.gemini_provider import GeminiStoryProvider


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text


class _FailingClient:
    def __init__(self, failures: int, payload: str):
        self.failures = failures
        self.payload = payload
        self.calls = 0

    class models:
        pass


def test_gemini_key_rotation(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY_1", "one")
    monkeypatch.setenv("GEMINI_API_KEY_2", "two")
    monkeypatch.setenv("GEMINI_API_KEY_3", "three")

    config = ProjectConfig.load("settings.yaml")
    provider = GeminiStoryProvider(config, __import__("logging").getLogger("test"))

    attempts = []

    class FakeModels:
        def __init__(self, client):
            self.client = client

        def generate_content(self, **kwargs):
            attempts.append(self.client.api_key)
            if self.client.api_key == "one":
                raise RuntimeError("quota")
            return _FakeResponse(
                '{"title":"x","monster":"Leshy","hook":"h","scenes":[{"index":1,"text":"a","image_prompt":"b"},{"index":2,"text":"a","image_prompt":"b"},{"index":3,"text":"a","image_prompt":"b"},{"index":4,"text":"a","image_prompt":"b"}],"ending_question":"q","social":{"youtube_title":"yt","youtube_description":"yd","instagram_caption":"ig","tiktok_caption":"tt","hashtags":["#t"]}}'
            )

    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key
            self.models = FakeModels(self)

    monkeypatch.setattr(provider.genai, "Client", FakeClient)

    story = provider.generate_story("Leshy")

    assert story.monster == "Leshy"
    assert attempts == ["one", "one", "one", "two"]
