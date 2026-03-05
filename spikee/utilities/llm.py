from typing import Dict, List

import os

EXAMPLE_LLM_MODELS = [
    "openai-gpt-4.1-mini",
    "openai-gpt-4o",
    "offline",
]

SUPPORTED_LLM_MODELS = [
    "llamaccp-server",
    "offline",
    "mock",
]

SUPPORTED_PREFIXES = [
    "openai-",
    "google-",
    "bedrock-",     # BedrockChat for Anthropic Models
    "bedrockcv-",   # BedrockChatConverse for other model compatibility
    "ollama-",
    "llamaccp-server-",
    "together-",
    "groq-",
    "deepseek-",
    "openrouter-",
    "azure-",
    "mock-",
]


def get_example_llm_models() -> List[str]:
    """Return the list of example LLM models."""
    return EXAMPLE_LLM_MODELS


def get_supported_llm_models() -> List[str]:
    """Return the list of supported LLM models."""
    return SUPPORTED_LLM_MODELS


def get_supported_prefixes() -> List[str]:
    """Return the list of supported LLM model prefixes."""
    return SUPPORTED_PREFIXES


# Map of shorthand keys to TogetherAI model identifiers
TOGETHER_AI_MODEL_MAP: Dict[str, str] = {
    "gemma2-8b": "google/gemma-2-9b-it",
    "gemma2-27b": "google/gemma-2-27b-it",
    "llama4-maverick-fp8": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
    "llama4-scout": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
    "llama31-8b": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "llama31-70b": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "llama31-405b": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    "llama33-70b": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "mixtral-8x7b": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "mixtral-8x22b": "mistralai/Mixtral-8x22B-Instruct-v0.1",
    "qwen3-235b-fp8": "Qwen/Qwen3-235B-A22B-fp8-tput",
}

# Default shorthand key
DEFAULT_TOGETHER_AI_KEY = "llama31-8b"

# Map of shorthand keys to AWS Bedrock model identifiers
BEDROCK_MODEL_MAP: Dict[str, str] = {
    "claude35-haiku": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "claude35-sonnet": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "claude37-sonnet": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
}


def _resolve_togetherai_model(key: str) -> str:
    """
    Convert a shorthand key to the full model identifier.
    Raises ValueError for unknown keys.
    """
    if key not in TOGETHER_AI_MODEL_MAP:
        valid = ", ".join(TOGETHER_AI_MODEL_MAP.keys())
        raise ValueError(f"Unknown model key '{key}'. Valid keys: {valid}")
    return TOGETHER_AI_MODEL_MAP[key]


def validate_llm_option(option: str) -> bool:
    """
    Validate if the provided options correspond to a supported LLM model.
    """
    if option is None:
        raise ValueError(
            "LLM option cannot be None, ensure than modules leveraging LLM utilities specify an LLM option."
        )

    return option in SUPPORTED_LLM_MODELS or any(
        option.startswith(prefix) for prefix in SUPPORTED_PREFIXES
    )


def get_llm(options=None, max_tokens=8, temperature=0) -> dict:
    """
    Constructs and returns kwargs for litellm.completion() based on options.

    Arguments:
        options (str): The LLM model option string.
        max_tokens (int): Maximum tokens for the LLM response (Default: 8 for LLM Judging).
        temperature (float): Sampling temperature for the LLM (Default: 0).
    """
    if not validate_llm_option(options):
        raise ValueError(
            f"Unsupported LLM option: '{options}'. "
            f"Supported Prefixes: {SUPPORTED_PREFIXES}, Supported Models: {SUPPORTED_LLM_MODELS}"
        )

    kwargs = {
        "temperature": temperature,
    }
    
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    if options.startswith("openai-"):
        model_name = options.replace("openai-", "")
        kwargs["model"] = f"openai/{model_name}"
        kwargs["num_retries"] = 2

    elif options.startswith("google-"):
        model_name = options.replace("google-", "")
        # litellm expects gemini/ or vertex_ai/ prefix, we use gemini for Google AI Studio
        kwargs["model"] = f"gemini/{model_name}"
        kwargs["num_retries"] = 2

    elif options.startswith("bedrock-"):
        model_name_key = options.replace("bedrock-", "")
        # Resolve shorthand key if it exists in the map
        model_name = BEDROCK_MODEL_MAP.get(model_name_key, model_name_key)
        kwargs["model"] = f"bedrock/{model_name}"

    elif options.startswith("bedrockcv-"):
        # LiteLLM handles converse vs standard natively via the AWS provider configuration.
        model_name = options.replace("bedrockcv-", "")
        kwargs["model"] = f"bedrock/{model_name}"
        if max_tokens is None:
            kwargs["max_tokens"] = 8192

    elif options.startswith("ollama-"):
        model_name = options.replace("ollama-", "")
        kwargs["model"] = f"ollama/{model_name}"
        timeout = os.environ.get("OLLAMA_TIMEOUT")
        if timeout:
            kwargs["timeout"] = float(timeout)
        attempts = os.environ.get("OLLAMA_MAX_ATTEMPTS")
        kwargs["num_retries"] = int(attempts) if attempts else 1

    elif options.startswith("llamaccp-server"):
        if options == "llamaccp-server":
            url = "http://localhost:8080/"
        else:
            try:
                port = int(options.split("llamaccp-server-")[-1])
                url = f"http://localhost:{port}/"
            except ValueError as e:
                raise ValueError(
                    f"Invalid port in options: '{options}'. Expected format 'llamaccp-server-[port]', for example 'llamaccp-server-8080'."
                ) from e
        kwargs["model"] = "openai/custom-model" # Litellm routes via openai base api handling
        kwargs["api_base"] = url
        kwargs["api_key"] = "abc"
        kwargs["num_retries"] = 2

    elif options.startswith("together-"):
        model_name_key = options.replace("together-", "")
        key = model_name_key if options is not None else DEFAULT_TOGETHER_AI_KEY
        model_name = _resolve_togetherai_model(key)
        kwargs["model"] = f"together_ai/{model_name}"
        kwargs["api_key"] = os.environ.get("TOGETHER_API_KEY")
        kwargs["num_retries"] = 2

    elif options.startswith("groq-"):
        model_name = options.replace("groq-", "")
        kwargs["model"] = f"groq/{model_name}"
        kwargs["num_retries"] = 2

    elif options.startswith("deepseek-"):
        model_name = options.replace("deepseek-", "")
        kwargs["model"] = f"deepseek/{model_name}"
        kwargs["num_retries"] = 2

    elif options.startswith("openrouter-"):
        model_name = options.replace("openrouter-", "")
        kwargs["model"] = f"openrouter/{model_name}"
        kwargs["num_retries"] = 2

    elif options.startswith("azure-"):
        model_name = options.replace("azure-", "")
        kwargs["model"] = f"azure/{model_name}"
        kwargs["api_version"] = os.environ.get("API_VERSION", "2024-05-01-preview")
        kwargs["num_retries"] = 2

    elif options.startswith("offline"):
        return None

    elif options == "mock":
        kwargs["model"] = "mock/gpt-3.5-turbo"
        mock_response = "This is a mock response from the LLM."
        if max_tokens is not None:
            mock_response = mock_response[:max_tokens]
        kwargs["mock_response"] = mock_response

    elif options.startswith("mock-"):
        real_model = options[5:]
        nested_kwargs = get_llm(real_model, max_tokens=max_tokens, temperature=temperature)
        return nested_kwargs # To natively intercept and print we should ideally use litellm.callbacks, but for simplicity we fallthrough to real

    else:
        raise ValueError(
            f"Invalid options format: '{options}'. Expected prefix 'openai-', 'google-', 'ollama-', 'bedrock-', 'llamaccp-server', 'together-', or 'offline'."
        )

    return kwargs
