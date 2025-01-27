import os
from langchain_aws import ChatBedrock
from dotenv import load_dotenv

load_dotenv()

llm = ChatBedrock(
    model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    model_kwargs=dict(temperature=0),
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
