"""
Thin wrapper around the LLM provider (OpenAI or Gemini) so the rest of the
app can call `call_llm(prompt)` without caring which provider is configured.
"""
from config import settings


def _call_openai(system_prompt: str, user_prompt: str) -> str:
    from openai import OpenAI

    if not settings.OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env file to use resume parsing."
        )

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    import google.generativeai as genai

    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your .env file to use resume parsing."
        )

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=system_prompt,
    )
    response = model.generate_content(user_prompt)
    return response.text


def call_llm(user_prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
    if settings.LLM_PROVIDER == "gemini":
        return _call_gemini(system_prompt, user_prompt)
    return _call_openai(system_prompt, user_prompt)
