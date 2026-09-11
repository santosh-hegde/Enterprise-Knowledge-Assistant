REWRITE_PROMPT = """Given the chat history and a follow-up question, rewrite the follow-up as a standalone search query.

If it is already standalone, return it unchanged.
Return only the query, nothing else.

Chat history:
{history}

Follow-up: {question}
"""

ANSWER_PROMPT = """You are Pinnacle Infotech's employee knowledge assistant.
Use only the document excerpts. If they do not contain the answer, say you could not find that in the company documents.
Do not invent amounts, days, names, or rules. If a detail is missing, say so.

Excerpts:
{context}

Question: {question}
"""

NOT_FOUND = "I could not find that in the company documents I have. Try asking about leave, travel, IT, benefits, or the code of conduct."
