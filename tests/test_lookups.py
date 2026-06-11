from seo_analyser.runner.lookups import models_method_name


def test_chat_gpt_maps_to_models():
    assert models_method_name("chat_gpt_llm_responses_live") == "chat_gpt_llm_responses_models"


def test_task_post_also_maps():
    assert models_method_name("claude_llm_responses_task_post") == "claude_llm_responses_models"


def test_all_llm_providers():
    for prefix in ("chat_gpt", "claude", "gemini", "perplexity"):
        assert models_method_name(f"{prefix}_llm_responses_live") == f"{prefix}_llm_responses_models"


def test_non_llm_returns_none():
    assert models_method_name("google_organic_live_advanced") is None
    assert models_method_name("chat_gpt_llm_responses_models") is None


def test_task_based_llm_responses_also_get_models_dropdown():
    from seo_analyser.runner.lookups import models_method_name
    # The folded task triplet drops the _live suffix; it still has the sibling.
    assert models_method_name("chat_gpt_llm_responses") == "chat_gpt_llm_responses_models"
    assert models_method_name("claude_llm_responses") == "claude_llm_responses_models"
    # The models endpoint itself must not self-match.
    assert models_method_name("chat_gpt_llm_responses_models") is None
