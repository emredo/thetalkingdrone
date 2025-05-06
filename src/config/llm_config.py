from langchain_google_genai import ChatGoogleGenerativeAI

from src.constant.keys import GOOGLE_API_KEY


def get_llm_object():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-pro-exp-03-25",
        temperature=0.2,
        google_api_key=GOOGLE_API_KEY,
    )
