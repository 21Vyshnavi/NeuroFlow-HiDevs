# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
import asyncio
import time
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI, RateLimitError

from backend.providers.base import BaseLLMProvider, ChatMessage, GenerationResult


class OpenAIProvider(BaseLLMProvider):
    # hardcoded price table per model (prices in USD per million tokens)
    PRICES = {
        "gpt-4o": {"input": 2.50, "output": 10.00, "context": 128000},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60, "context": 128000},
        "text-embedding-3-small": {"input": 0.02, "output": 0.0, "context": 8191}
    }

    def __init__(self, model_name: str = "gpt-4o-mini", api_key: str = "mock-key", base_url: str = None) -> None:
        self.model_name = model_name
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    @property
    def cost_per_input_token(self) -> float:
        return self.PRICES.get(self.model_name, self.PRICES["gpt-4o-mini"])["input"] / 1_000_000.0

    @property
    def cost_per_output_token(self) -> float:
        return self.PRICES.get(self.model_name, self.PRICES["gpt-4o-mini"])["output"] / 1_000_000.0

    @property
    def context_window(self) -> int:
        return self.PRICES.get(self.model_name, self.PRICES["gpt-4o-mini"])["context"]

    async def _execute_with_retry(self, func, *args, **kwargs):
        retries = 3
        backoff = 1.0
        for attempt in range(retries):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                if attempt == retries - 1:
                    raise e
                # Get retry header or default backoff
                retry_after = 2.0 * backoff
                await asyncio.sleep(retry_after)
                backoff *= 2.0
            except Exception as e:
                raise e

    async def complete(self, messages: list[ChatMessage], **kwargs) -> GenerationResult:
        formatted = [{"role": m.role, "content": m.content} for m in messages]
        
        async def call():
            return await self.client.chat.completions.create(
                model=self.model_name,
                messages=formatted,
                **kwargs
            )
            
        start_time = time.time()
        response = await self._execute_with_retry(call)
        latency = (time.time() - start_time) * 1000

        content = response.choices[0].message.content or ""
        in_tokens = response.usage.prompt_tokens
        out_tokens = response.usage.completion_tokens
        cost = (in_tokens * self.cost_per_input_token) + (out_tokens * self.cost_per_output_token)
        
        return GenerationResult(
            content=content,
            model=self.model_name,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            latency_ms=latency,
            cost_usd=cost,
            finish_reason=response.choices[0].finish_reason or "stop"
        )

    async def stream(self, messages: list[ChatMessage], **kwargs) -> AsyncGenerator[str, None]:
        formatted = [{"role": m.role, "content": m.content} for m in messages]
        
        async def call():
            return await self.client.chat.completions.create(
                model=self.model_name,
                messages=formatted,
                stream=True,
                **kwargs
            )
        
        response = await self._execute_with_retry(call)
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # text-embedding-3-small batching of 100
        batch_size = 100
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            async def call():
                return await self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=batch
                )
            res = await self._execute_with_retry(call)
            embeddings.extend([d.embedding for d in res.data])
        return embeddings
