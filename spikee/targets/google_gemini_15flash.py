import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
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
        return ai_msg.content
    except Exception as e:
        print(f"Error during LLM completion: {e}")
        raise
