import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

llm = ChatOpenAI(
    model="o3",
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

def process_input(input_text, system_message=None):
    messages = []
    # system message not supported by o1 models at this time
    # so we just add the system message at the beginning
    prompt = input_text
    if system_message:
       prompt = f"{system_message}\n{input_text}"

    messages.append(("user", prompt))
    
    try:
        ai_msg = llm.invoke(messages)
        return ai_msg.content
    except Exception as e:
        print(f"Error during LLM completion: {e}")
        raise

