import time
import asyncio
from typing import AsyncGenerator
from anthropic import AsyncAnthropic, RateLimitError
from backend.providers.base import BaseLLMProvider, ChatMessage, GenerationResult

class AnthropicProvider(BaseLLMProvider):
    # Prices in USD per million tokens
    PRICES = {
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00, "context": 200000},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25, "context": 200000}
    }

    def __init__(self, model_name: str = "claude-3-haiku-20240307", api_key: str = "mock-key"):
        self.model_name = model_name
        self.client = AsyncAnthropic(api_key=api_key)

    @property
    def cost_per_input_token(self) -> float:
        return self.PRICES.get(self.model_name, self.PRICES["claude-3-haiku-20240307"])["input"] / 1_000_000.0

    @property
    def cost_per_output_token(self) -> float:
        return self.PRICES.get(self.model_name, self.PRICES["claude-3-haiku-20240307"])["output"] / 1_000_000.0

    @property
    def context_window(self) -> int:
        return self.PRICES.get(self.model_name, self.PRICES["claude-3-haiku-20240307"])["context"]

    async def _execute_with_retry(self, func, *args, **kwargs):
        retries = 3
        backoff = 1.0
        for attempt in range(retries):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                if attempt == retries - 1:
                    raise e
                retry_after = 2.0 * backoff
                await asyncio.sleep(retry_after)
                backoff *= 2.0
            except Exception as e:
                raise e

    def _parse_messages(self, messages: list[ChatMessage]):
        system_prompt = None
        formatted = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                formatted.append({"role": m.role, "content": m.content})
        return system_prompt, formatted

    async def complete(self, messages: list[ChatMessage], **kwargs) -> GenerationResult:
        system_prompt, formatted = self._parse_messages(messages)
        
        async def call():
            params = {
                "model": self.model_name,
                "messages": formatted,
                **kwargs
            }
            if system_prompt:
                params["system"] = system_prompt
            return await self.client.messages.create(**params)

        start_time = time.time()
        response = await self._execute_with_retry(call)
        latency = (time.time() - start_time) * 1000

        content = response.content[0].text if response.content else ""
        in_tokens = response.usage.input_tokens
        out_tokens = response.usage.output_tokens
        cost = (in_tokens * self.cost_per_input_token) + (out_tokens * self.cost_per_output_token)

        return GenerationResult(
            content=content,
            model=self.model_name,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            latency_ms=latency,
            cost_usd=cost,
            finish_reason=response.stop_reason or "stop"
        )

    async def stream(self, messages: list[ChatMessage], **kwargs) -> AsyncGenerator[str, None]:
        system_prompt, formatted = self._parse_messages(messages)
        
        async def call():
            params = {
                "model": self.model_name,
                "messages": formatted,
                **kwargs
            }
            if system_prompt:
                params["system"] = system_prompt
            return self.client.messages.stream(**params)

        stream_ctx = await self._execute_with_retry(call)
        async with stream_ctx as stream:
            async for text in stream.text_stream:
                yield text

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Anthropic does not support native embeddings; standard to throw or delegate to OpenAI
        raise NotImplementedError("Anthropic does not offer embeddings API natively. Use OpenAIProvider for embeddings.")
