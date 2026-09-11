from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from src.config import CHAT_MODEL, EMBED_MODEL, gemini_api_key


def chat_llm():
    return ChatGoogleGenerativeAI(
        model=CHAT_MODEL,
        temperature=0,
        google_api_key=gemini_api_key(),
    )


def embeddings():
    return GoogleGenerativeAIEmbeddings(
        model=EMBED_MODEL,
        google_api_key=gemini_api_key(),
    )


def response_text(msg) -> str:
    content = msg.content
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        bits = []
        for part in content:
            if isinstance(part, str):
                bits.append(part)
            elif isinstance(part, dict) and part.get("text"):
                bits.append(part["text"])
        return "".join(bits).strip()
    return str(content).strip()
