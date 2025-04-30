import os
from langchain_together import ChatTogether
from dotenv import load_dotenv
import re

load_dotenv()

def strip_thoughts(text: str) -> str:
    # Matches one or more <think>…</think> blocks (with any whitespace around them)
    # only at the very start of the string, including multiline content.
    pattern = r'^(?:\s*<think>[\s\S]*?<\/think>\s*)+'
    return re.sub(pattern, '', text)

llm = ChatTogether(
    model="Qwen/Qwen3-235B-A22B-fp8-tput",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

def process_input(input_text, system_message=None):
    messages = []
    if system_message:
        messages.append(("system", system_message))
    messages.append(("user", input_text))
    
    try:
        ai_msg = llm.invoke(messages)
        # We do not want to include thoughts in the output
        return strip_thoughts(ai_msg.content)
    except Exception as e:
        print(f"Error during LLM completion: {e}")
        raise
