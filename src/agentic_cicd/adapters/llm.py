from ..core.interfaces import LLMProvider
from langchain_google_genai import ChatGoogleGenerativeAI
from ..config import settings

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.llm_model
        self.llm = ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=self.api_key,
            temperature=0
        )

    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.llm.ainvoke(prompt)
        return response.content


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        raise NotImplementedError("OpenAI provider not yet implemented")

def get_llm_provider():
    if settings.llm_provider == "gemini":
        return GeminiProvider()
    elif settings.llm_provider == "openai":
        return OpenAIProvider(settings.llm_api_key)
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")