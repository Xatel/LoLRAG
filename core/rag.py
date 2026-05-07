async def query_rag(query: str, session_id: str | None = None) -> tuple[str, list[str]]:
    # TODO: implement retrieval + generation pipeline
    answer = f"Echo: {query}"
    sources: list[str] = []
    return answer, sources
