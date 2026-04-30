from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader

from app.config import settings


try:
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
except Exception:

    class TextLoader:
        def __init__(self, file_path: str, encoding: str = "utf-8"):
            self.file_path = file_path
            self.encoding = encoding

        def load(self) -> list[Document]:
            text = Path(self.file_path).read_text(encoding=self.encoding)
            return [Document(page_content=text, metadata={"source": self.file_path})]

    class PyPDFLoader:
        def __init__(self, file_path: str):
            self.file_path = file_path

        def load(self) -> list[Document]:
            reader = PdfReader(self.file_path)
            docs: list[Document] = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                docs.append(
                    Document(
                        page_content=page_text,
                        metadata={"source": self.file_path, "page": i},
                    )
                )
            return docs


class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents: list[Document]) -> list[Document]:
        chunks: list[Document] = []
        for doc in documents:
            text = doc.page_content or ""
            start = 0
            chunk_index = 0

            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                chunk_text = text[start:end]

                metadata = dict(doc.metadata or {})
                metadata["chunk_index"] = chunk_index
                chunks.append(Document(page_content=chunk_text, metadata=metadata))

                chunk_index += 1
                if end == len(text):
                    break
                start = end - self.chunk_overlap

        return chunks


def load_and_chunk_documents(data_dir: str) -> list:
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    file_paths: list[Path] = []
    for file_path in data_path.rglob("*"):
        if not file_path.is_file():
            continue
        if any(part.startswith(".") for part in file_path.parts):
            continue
        suffix = file_path.suffix.lower()
        if suffix in {".txt", ".pdf"}:
            file_paths.append(file_path)

    file_paths = sorted(file_paths)
    if not file_paths:
        raise FileNotFoundError(f"No .txt or .pdf files found under: {data_dir}")

    all_docs = []
    for file_path in file_paths:
        suffix = file_path.suffix.lower()
        if suffix == ".txt":
            loader = TextLoader(str(file_path), encoding="utf-8")
        elif suffix == ".pdf":
            loader = PyPDFLoader(str(file_path))
        else:
            continue

        all_docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_documents(all_docs)
    print(f"Created {len(chunks)} chunks from {len(file_paths)} files.")
    return chunks
