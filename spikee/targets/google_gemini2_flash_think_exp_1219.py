import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-thinking-exp-1219",
  generation_config=generation_config,
)

def process_input(input_text, system_message=None):
    chat_session = model.start_chat()
    prompt = input_text
    if system_message:
        prompt = f"{system_message}\n{input_text}"

    try:
        response = chat_session.send_message(prompt)
        return response.text
    except Exception as e:
        print(f"Error during LLM completion: {e}")
        raise
