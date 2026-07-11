from core.config import ProjectConfig


def test_gemini_keys_env_list(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEYS", "alpha, beta; gamma\nalpha")
    monkeypatch.delenv("GEMINI_API_KEY_1", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY_2", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY_3", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    config = ProjectConfig.load("settings.yaml", load_env=False)

    assert config.gemini_api_keys == ["alpha", "beta", "gamma"]
