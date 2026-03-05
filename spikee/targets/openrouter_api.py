"""
spikee/targets/openrouter_api.py

Unified OpenRouter target that invokes models based on a simple string key.

Usage:
    target_options: str, one of the model IDs returned by get_available_option_values() or any valid OpenRouter model.
    If None, DEFAULT_MODEL is used.

Exposed:
    get_available_option_values() -> list of supported model IDs (default marked)
    process_input(input_text, system_message=None, target_options=None) -> response content
"""

import os
from spikee.templates.target import Target
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()


class OpenRouterTarget(Target):
    # Some popular OpenRouter models for convenience
    _SUPPORTED_MODELS: List[str] = [
        "google/gemini-2.5-flash",
        "anthropic/claude-3.5-haiku",
        "meta-llama/llama-3.1-8b-instruct",
        "openai/gpt-4o-mini",
    ]

    # Default model ID
    DEFAULT_MODEL = "google/gemini-2.5-flash"

    def get_available_option_values(self) -> List[str]:
        """Return supported model IDs; first option is default."""
        options = [self.DEFAULT_MODEL]  # Default first
        options.extend([m for m in self._SUPPORTED_MODELS if m != self.DEFAULT_MODEL])
        return options

    def process_input(
        self,
        input_text: str,
        system_message: Optional[str] = None,
        target_options: Optional[str] = None,
    ) -> str:
        """
        Send messages to OpenRouter based on the designated model name.
        """
        # Model selection
        model_name = (
            target_options if target_options is not None else self.DEFAULT_MODEL
        )

        # Build messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": input_text})

        # Invoke model
        try:
            import litellm

            response = litellm.completion(
                model=f"openrouter/{model_name}",
                api_key=os.environ.get("OPENROUTER_API_KEY"),
                messages=messages,
                temperature=0,
                num_retries=2,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error during OpenRouter completion ({model_name}): {e}")
            raise

if __name__ == "__main__":
    target = OpenRouterTarget()
    print("Supported models:", target.get_available_option_values())
    try:
        out = target.process_input("Hello!", target_options="google/gemini-2.5-flash")
        print(out)
    except Exception as err:
        print("Error:", err)
