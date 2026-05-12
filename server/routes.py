from fastapi import APIRouter
from pydantic import BaseModel
from rag.rag import query_rag

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[str] = []


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    answer, sources = await query_rag(request.query, request.session_id)
    return QueryResponse(answer=answer, sources=sources)
