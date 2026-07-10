# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
import logging
from collections.abc import AsyncGenerator

import redis.asyncio as redis
from opentelemetry import trace

from backend.config import settings
from backend.providers.anthropic_provider import AnthropicProvider
from backend.providers.base import BaseLLMProvider, ChatMessage, GenerationResult
from backend.providers.openai_provider import OpenAIProvider
from backend.providers.router import ModelConfig, ModelRouter, RoutingCriteria

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("neuroflow.llm_client")

class NeuroFlowClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self.router = ModelRouter()
        self._providers: dict[str, BaseLLMProvider] = {}
        self._initialized = True

    def _get_provider(self, config: ModelConfig) -> BaseLLMProvider:
        key = f"{config.provider}:{config.model_name}"
        if key not in self._providers:
            if config.provider == "openai":
                self._providers[key] = OpenAIProvider(model_name=config.model_name)
            elif config.provider == "anthropic":
                self._providers[key] = AnthropicProvider(model_name=config.model_name)
            else:
                raise ValueError(f"Unknown provider: {config.provider}")
        return self._providers[key]

    async def _increment_metrics(self, model: str, cost: float, provider: str = "unknown", task_type: str = "generation") -> None:
        try:
            r = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password
            )
            await r.incr(f"metrics:model:{model}:calls")
            await r.incrbyfloat(f"metrics:model:{model}:cost_usd", cost)
            await r.aclose()
        except Exception as e:
            logger.error(f"Failed to write metrics to Redis: {e}")
            
        try:
            from backend.monitoring.metrics import llm_cost, lm_calls_total
            lm_calls_total.labels(provider=provider, model=model, task_type=task_type).inc()
            llm_cost.labels(model=model).observe(cost)
        except ImportError:
            pass

    async def chat(self, messages: list[ChatMessage], criteria: RoutingCriteria, **kwargs) -> GenerationResult:
        model_config = await self.router.route(criteria)
        provider = self._get_provider(model_config)

        with tracer.start_as_current_span("llm_call") as span:
            span.set_attribute("model", model_config.model_name)
            span.set_attribute("provider", model_config.provider)
            
            # Simple list of fallbacks for reliability (gpt-4o-mini -> claude-3-haiku-20240307 -> gpt-4o)
            fallback_chain = ["gpt-4o-mini", "claude-3-haiku-20240307", "gpt-4o"]
            
            last_err = None
            for model_name in [model_config.model_name] + fallback_chain:
                try:
                    if model_name != model_config.model_name:
                        # Create fallback config
                        temp_config = ModelConfig(
                            model_name=model_name,
                            provider="openai" if "gpt" in model_name else "anthropic",
                            is_vision=True,
                            context_limit=128000,
                            estimated_input_cost=0.15,
                            estimated_output_cost=0.60
                        )
                        provider = self._get_provider(temp_config)
                    
                    res = await provider.complete(messages, **kwargs)
                    
                    # Record span attributes
                    span.set_attribute("input_tokens", res.input_tokens)
                    span.set_attribute("output_tokens", res.output_tokens)
                    span.set_attribute("cost_usd", res.cost_usd)
                    span.set_attribute("latency_ms", res.latency_ms)
                    
                    await self._increment_metrics(res.model, res.cost_usd, provider=provider.__class__.__name__)
                    return res
                except Exception as e:
                    logger.warning(f"Model call failed for {model_name}. Error: {e}. Trying next fallback...")
                    last_err = e
            
            raise last_err

    async def stream(self, messages: list[ChatMessage], criteria: RoutingCriteria, **kwargs) -> AsyncGenerator[str, None]:
        model_config = await self.router.route(criteria)
        provider = self._get_provider(model_config)

        # Basic streaming fallback
        try:
            async for token in provider.stream(messages, **kwargs):
                yield token
        except Exception as e:
            logger.warning(f"Streaming failed on primary. Falling back to default: {e}")
            fallback_config = ModelConfig(
                model_name="gpt-4o-mini",
                provider="openai",
                is_vision=True,
                context_limit=128000,
                estimated_input_cost=0.15,
                estimated_output_cost=0.60
            )
            fallback_provider = self._get_provider(fallback_config)
            async for token in fallback_provider.stream(messages, **kwargs):
                yield token

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Default embedder uses OpenAI text-embedding-3-small
        provider = OpenAIProvider(model_name="text-embedding-3-small")
        return await provider.embed(texts)

client = NeuroFlowClient()
