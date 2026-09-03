from ollama import chat

from .prompts import SYSTEM_PROMPT


def ask_ai(question):
    response = chat(
    model="gemma3:1b",
    messages=[
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": question
        }
        ],
    options={
        "num_predict": 80
    }
    )

    return response.message.content