import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o",
    max_tokens=None,
    timeout=None,
    max_retries=2,
).bind(logprobs=True)

def process_input(input_text, system_message=None):
    messages = []
    if system_message:
        messages.append(("system", system_message))
    messages.append(("user", input_text))

    try:
        ai_msg = llm.invoke(messages)
        return ai_msg.content, ai_msg.response_metadata["logprobs"]
    except Exception as e:
        print(f"Error during LLM completion: {e}")
        raise

