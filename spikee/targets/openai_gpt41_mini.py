import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def process_input(input_text, system_message=None, logprobs=False):  
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        max_tokens=None,
        timeout=None,
        max_retries=2,
    ).bind(logprobs=logprobs)

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

