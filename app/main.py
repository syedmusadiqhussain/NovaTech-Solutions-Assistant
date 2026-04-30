from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

from app.embedder import build_vector_store
from app.loader import load_and_chunk_documents
from app.rag_pipeline import get_rag_response


class ChatRequest(BaseModel):
    question: str


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_STATIC_DIR = Path(__file__).resolve().parent / "static"
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.on_event("startup")
def _startup_log() -> None:
    try:
        import sys

        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("🚀 RAG Chatbot API started. Visit /docs for Swagger UI.")


@app.exception_handler(Exception)
async def _global_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/")
def root() -> dict:
    return {"status": "ok", "message": "RAG Chatbot API is running"}

@app.get("/ui")
def ui() -> FileResponse:
    index_path = _STATIC_DIR / "index.html"
    if not index_path.exists():
        raise FileNotFoundError("UI not found. Expected app/static/index.html")
    return FileResponse(str(index_path), media_type="text/html")


@app.get("/health")
def health() -> dict:
    index_dir = Path("vector_store") / "faiss_index"
    index_loaded = (index_dir / "index.faiss").exists() and (index_dir / "index.pkl").exists()
    return {"status": "healthy", "vector_store": "loaded" if index_loaded else "not_found"}


@app.post("/chat")
def chat(req: ChatRequest) -> dict:
    return get_rag_response(req.question)


@app.post("/ingest")
def ingest() -> dict:
    chunks = load_and_chunk_documents("data/")
    build_vector_store(chunks)
    return {"status": "success", "chunks_indexed": len(chunks)}
