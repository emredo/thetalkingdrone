from langchain_google_genai import ChatGoogleGenerativeAI

from src.constant.keys import GOOGLE_API_KEY
from src.utils.logger import logger


def get_llm_object():
    try:
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-preview-05-20",
            temperature=0.2,
            google_api_key=GOOGLE_API_KEY,
        )
    except Exception as e:
        logger.error(f"Error getting LLM object: {e}")
        raise Exception(f"Error getting LLM object: {e}")
