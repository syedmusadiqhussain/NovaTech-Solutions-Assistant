from langchain_openai import ChatOpenAI

from app.config import settings
from app.embedder import load_vector_store


def get_rag_response(question: str) -> dict:
    vector_store = load_vector_store()
    retrieved_chunks = vector_store.similarity_search(
        question,
        k=settings.top_k_results,
    )

    retrieved_context = "\n\n".join([doc.page_content for doc in retrieved_chunks])

    prompt = (
        "System: You are a helpful AI assistant. Answer the user's question using ONLY the context provided below.\n"
        'If the answer is not found in the context, say: "I don\'t have information about that in my knowledge base."\n'
        "Do NOT make up information.\n\n"
        "Context:\n"
        f"{retrieved_context}\n\n"
        f"User Question: {question}\n\n"
        "Answer:\n"
    )

    api_key = settings.openrouter_api_key or (settings.openai_api_key if settings.use_openai else "")
    if settings.use_local_llm or not api_key:
        if not retrieved_chunks:
            llm_response = "I don't have information about that in my knowledge base."
        else:
            llm_response = retrieved_chunks[0].page_content.strip()
    else:
        base_url = settings.openrouter_base_url if settings.openrouter_api_key else None
        llm = ChatOpenAI(model=settings.llm_model, temperature=0, api_key=api_key, base_url=base_url)
        llm_response = llm.invoke(prompt).content

    return {
        "question": question,
        "answer": llm_response,
        "sources": [doc.metadata for doc in retrieved_chunks],
    }
