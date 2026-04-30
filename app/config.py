import os

from dotenv import load_dotenv
from pydantic.v1 import BaseSettings, Field


load_dotenv()


class Settings(BaseSettings):
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    openrouter_api_key: str = Field("", env="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")
    embedding_model: str = Field("nomic-ai/nomic-embed-text-v1.5", env="EMBEDDING_MODEL")
    llm_model: str = Field("meta-llama/llama-3.1-8b-instruct:free", env="LLM_MODEL")
    use_openai: bool = Field(False, env="USE_OPENAI")
    use_local_embeddings: bool = Field(False, env="USE_LOCAL_EMBEDDINGS")
    local_embedding_dim: int = Field(512, env="LOCAL_EMBEDDING_DIM")
    use_local_llm: bool = Field(False, env="USE_LOCAL_LLM")
    chunk_size: int = Field(500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(50, env="CHUNK_OVERLAP")
    top_k_results: int = Field(4, env="TOP_K_RESULTS")

    class Config:
        case_sensitive = False


settings = Settings()

effective_api_key = settings.openrouter_api_key or (settings.openai_api_key if settings.use_openai else "")
if settings.openrouter_api_key and not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
