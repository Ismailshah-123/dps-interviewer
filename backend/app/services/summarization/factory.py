from .base import SummarizationProvider
from .ollama import OllamaProvider
from .deterministic import DeterministicSummarizationProvider
from .groq_provider import GroqSummarizationProvider

class UnavailableSummarizationProvider(SummarizationProvider):
    name = "unavailable"
    async def summarize(self, transcript: str, segments: list[dict]):
        raise RuntimeError("No summarization provider is configured. Set SUMMARIZATION_PROVIDER=ollama and configure Ollama.")

def get_summarization_provider() -> SummarizationProvider:
    from app.core.config import settings
    if settings.summarization_provider == 'deterministic-test': return DeterministicSummarizationProvider()
    if settings.summarization_provider == 'ollama': return OllamaProvider()
    if settings.summarization_provider == 'groq': return GroqSummarizationProvider()
    return UnavailableSummarizationProvider()
