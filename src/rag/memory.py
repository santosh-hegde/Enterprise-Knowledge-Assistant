from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.messages import get_buffer_string, trim_messages

from src.config import MEMORY_WINDOW


def new_memory() -> InMemoryChatMessageHistory:
    return InMemoryChatMessageHistory()


def windowed_messages(history: BaseChatMessageHistory):
    return trim_messages(
        history.messages,
        max_tokens=MEMORY_WINDOW * 2,
        token_counter=len,
        strategy="last",
        start_on="human",
    )


def history_text(history: BaseChatMessageHistory) -> str:
    return get_buffer_string(
        windowed_messages(history),
        human_prefix="User",
        ai_prefix="Assistant",
    )
