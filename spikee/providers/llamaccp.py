from spikee.providers.custom import AnyLLMCustomProvider
import os


class AnyLLMLLAMACCPProvider(AnyLLMCustomProvider):
    """AnyLLM provider for LLAMA CCP models (via Custom provider with OpenAI compatibility)"""

    @property
    def name(self) -> str:
        return "LLAMA CCP"

    @property
    def base_url(self) -> str:
        return os.getenv("LLAMACCP_URL", "http://localhost:8080/")

    @property
    def api_key(self) -> str:
        return "abc"
