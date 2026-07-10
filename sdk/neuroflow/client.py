import httpx
import json
from pathlib import Path
from typing import AsyncGenerator, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .models import Document, QueryResult, EvaluationResult

class NeuroFlowError(Exception):
    pass

class RateLimitError(NeuroFlowError):
    pass

class NeuroFlowClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(5)
    )
    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        response = await self.client.request(method, path, **kwargs)
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded (429)")
        response.raise_for_status()
        return response

    async def ingest_file(self, file_path: str | Path, pipeline_id: Optional[str] = None) -> Document:
        """Upload and ingest a file."""
        file_path = Path(file_path)
        data = {"pipeline_id": pipeline_id} if pipeline_id else {}
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f)}
            res = await self._request("POST", "/ingest", files=files, data=data)
        return Document(**res.json())

    async def ingest_url(self, url: str, pipeline_id: Optional[str] = None) -> Document:
        """Ingest a URL."""
        data = {"url": url}
        if pipeline_id:
            data["pipeline_id"] = pipeline_id
        res = await self._request("POST", "/ingest/url", json=data)
        return Document(**res.json())

    async def query(self, query: str, pipeline_id: str, stream: bool = False) -> QueryResult | AsyncGenerator[str, None]:
        """Run a RAG query. Returns AsyncGenerator if stream=True."""
        data = {"query": query, "pipeline_id": pipeline_id, "stream": stream}
        if stream:
            return self._query_stream(data)
        res = await self._request("POST", "/query", json=data)
        return QueryResult(**res.json())

    async def _query_stream(self, data: dict) -> AsyncGenerator[str, None]:
        async with self.client.stream("POST", "/query", json=data) as response:
            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield line[6:]

    async def get_evaluation(self, run_id: str, wait: bool = True) -> EvaluationResult:
        """Get evaluation results for a query run."""
        res = await self._request("GET", f"/evaluations/{run_id}")
        return EvaluationResult(**res.json())

    async def list_pipelines(self) -> list[dict]:
        res = await self._request("GET", "/pipelines")
        return res.json()

    async def create_pipeline(self, config: dict) -> dict:
        res = await self._request("POST", "/pipelines", json=config)
        return res.json()

    async def close(self):
        await self.client.aclose()
