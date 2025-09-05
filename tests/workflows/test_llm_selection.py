from app.workflows import llm
from app.workflows.models import LLM_MODELS


def test_chat_model_uses_configured_model(monkeypatch):
    captured = {}

    def fake_init_chat_model(*, model):
        captured["model"] = model

        class Dummy:
            pass

        return Dummy()

    monkeypatch.setattr(llm, "init_chat_model", fake_init_chat_model)
    monkeypatch.setattr(llm.settings, "llm_model", "azure")

    llm.chat_model()

    assert captured["model"] == LLM_MODELS["azure"]

