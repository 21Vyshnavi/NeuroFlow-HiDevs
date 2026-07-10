# NeuroFlow SDK

Python SDK for the NeuroFlow Multi-Modal LLM Orchestration Platform.

## Installation

```bash
pip install ./sdk
```

## Quickstart

```python
import asyncio
from neuroflow import NeuroFlowClient

async def main():
    client = NeuroFlowClient(base_url="http://localhost:8000", api_key="YOUR_TOKEN")
    
    # 1. Ingest a file
    doc = await client.ingest_file("sample.pdf", pipeline_id="default")
    print(f"Ingested: {doc.id}")
    
    # 2. Run a streaming query
    async for token in await client.query("What is in the document?", pipeline_id="default", stream=True):
        print(token, end="", flush=True)

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```
