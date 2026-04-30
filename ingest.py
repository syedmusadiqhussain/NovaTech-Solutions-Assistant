import argparse

from app.embedder import build_vector_store
from app.loader import load_and_chunk_documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest documents and build the FAISS vector store.")
    parser.add_argument("--data-dir", default="data/", help="Directory containing .txt and .pdf files")
    args = parser.parse_args()

    chunks = load_and_chunk_documents(args.data_dir)
    build_vector_store(chunks)
    print(f"✅ Vector store built and saved successfully. {len(chunks)} chunks indexed.")


if __name__ == "__main__":
    main()
