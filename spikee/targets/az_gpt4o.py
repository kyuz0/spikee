import os
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up the AzureChatOpenAI client with configuration from environment variables
llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_GPT4O_DEPLOYMENT_NAME", "gpt-4o"),
    api_version=os.getenv("API_VERSION", "2024-05-01-preview"),
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
