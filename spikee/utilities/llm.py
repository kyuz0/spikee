SUPPORTED_LLM_MODELS = [
    "openai-gpt-4.1-mini",
    "openai-gpt-4o-mini",

    "ollama-phi4-mini",
    "ollama-gemma3",
    "ollama-llama3.2",

    "bedrock-us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "bedrock-us.meta.llama4-scout-17b-instruct-v1:0",

    "llamaccp-server",
    "llamaccp-server-[port]",

    "offline",
]

SUPPORTED_PREFIXES = ["openai-", "ollama-", "bedrock-", "llamaccp-server-"]


def get_llm(options=None):
    """
    Initialize and return the appropriate LLM based on options.
    """
    if (options not in SUPPORTED_LLM_MODELS and not any(options.startswith(prefix) for prefix in SUPPORTED_PREFIXES)):
        raise ValueError(
            f"Unsupported LLM option: '{options}'. "
            f"Supported options: {SUPPORTED_LLM_MODELS}"
        )

    if options.startswith("openai-"):
        from langchain_openai import ChatOpenAI

        model_name = options.replace("openai-", "")
        return ChatOpenAI(
            model=model_name,
            max_tokens=8,
            temperature=0,
            timeout=None,
            max_retries=2,
        )

    elif options.startswith("ollama-"):
        from langchain_ollama import ChatOllama

        model_name = options.replace("ollama-", "")
        return ChatOllama(
            model=model_name,
            max_tokens=8,
            temperature=0,
            timeout=None,
            max_retries=2,
        )

    elif options.startswith("bedrock-"):
        from langchain_aws import ChatBedrock

        model_name = options.replace("bedrock-", "")
        return ChatBedrock(
            model=model_name,
            max_tokens=8,
            temperature=0
        )

    elif options.startswith("llamaccp-server"):
        from langchain_openai import ChatOpenAI

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

        return ChatOpenAI(
            base_url=url,
            api_key="abc",
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

    elif options.startswith("offline"):
        return None

    else:
        raise ValueError(
            f"Invalid options format: '{options}'. Expected prefix 'openai-', 'ollama-', 'bedrock-', 'llamaccp-server', or 'offline'."
        )
