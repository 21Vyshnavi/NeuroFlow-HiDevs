def build_prompt(query_type: str, context: str, query: str) -> str:
    base = (
        "You are a precise research assistant. Answer the user's question using ONLY the provided context.\n"
        "If the context does not contain enough information to answer fully, say so explicitly.\n"
        "For every factual claim, include a citation in the format [Source N].\n"
        "Do not introduce information not present in the context.\n"
    )
    
    additions = {
        "factual": "Provide a direct, concise answer. If multiple sources agree, cite all of them.",
        "analytical": "Analyze and synthesize across the provided sources. Identify agreements and contradictions.",
        "comparative": "Organize your response as a structured comparison. Use a table if appropriate.",
        "procedural": "Provide numbered steps. Each step must be cited."
    }
    
    addition = additions.get(query_type, additions["factual"])
    
    return f"{base}\n{addition}\n\n<context>\n{context}\n</context>\n\nQuery: {query}"
