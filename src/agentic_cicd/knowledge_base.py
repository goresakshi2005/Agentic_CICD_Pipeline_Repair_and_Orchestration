import os
import json
import logging
from datetime import datetime
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from .config import settings
from .database import SessionLocal, FixKnowledge

logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self):
        self.embeddings = None
        if settings.llm_provider == "gemini":
            try:
                self.embeddings = GoogleGenerativeAIEmbeddings(
                    model="text-embedding-004",
                    google_api_key=settings.llm_api_key
                )
            except Exception as e:
                logger.warning(f"Could not initialize embeddings: {e}")
        self.vector_store_path = "faiss_index"
        self.store = self._get_vector_store()

    def _get_vector_store(self):
        """Return a vector store (FAISS if available, else in-memory fallback)."""
        class InMemoryVectorStore:
            def __init__(self, docs=None):
                self.docs = docs or []

            def add_documents(self, docs):
                self.docs.extend(docs)

            def similarity_search(self, query, k=3):
                q_tokens = set(query.lower().split())
                scored = []
                for d in self.docs:
                    text = d.page_content
                    score = len(q_tokens.intersection(set(text.lower().split())))
                    scored.append((score, d))
                scored.sort(key=lambda x: x[0], reverse=True)
                return [d for _, d in scored[:k]]

            def save_local(self, path):
                os.makedirs(path, exist_ok=True)
                data = [{"page_content": d.page_content, "metadata": d.metadata} for d in self.docs]
                with open(os.path.join(path, "in_memory_store.json"), "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            @classmethod
            def load_local(cls, path, *args, **kwargs):
                file = os.path.join(path, "in_memory_store.json")
                if not os.path.exists(file):
                    return cls()
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                docs = [Document(page_content=item["page_content"], metadata=item["metadata"]) for item in data]
                return cls(docs=docs)

        if os.path.exists(self.vector_store_path):
            if self.embeddings is not None:
                try:
                    return FAISS.load_local(self.vector_store_path, self.embeddings, allow_dangerous_deserialization=True)
                except Exception as e:
                    logger.warning(f"Failed to load FAISS, using in-memory fallback: {e}")
                    return InMemoryVectorStore.load_local(self.vector_store_path)
            else:
                return InMemoryVectorStore.load_local(self.vector_store_path)

        if self.embeddings is not None:
            try:
                return FAISS.from_texts(["Placeholder"], self.embeddings)
            except Exception as e:
                logger.warning(f"FAISS.from_texts failed, using in-memory fallback: {e}")
                return InMemoryVectorStore([Document(page_content="Placeholder")])
        else:
            return InMemoryVectorStore([Document(page_content="Placeholder")])

    def add_fix(self, problem: str, solution: str, fix_type: str, success: bool = True, pr_url: str = None):
        doc = Document(
            page_content=f"Problem: {problem}\nSolution: {solution}",
            metadata={"fix_type": fix_type, "success": success, "timestamp": datetime.utcnow().isoformat(), "pr_url": pr_url}
        )
        self.store.add_documents([doc])
        self.store.save_local(self.vector_store_path)

        # Also store in SQL
        db = SessionLocal()
        sig = problem[:255]
        existing = db.query(FixKnowledge).filter_by(problem_signature=sig).first()
        if existing:
            existing.success_count += 1 if success else 0
        else:
            db.add(FixKnowledge(
                problem_signature=sig,
                solution=solution,
                fix_type=fix_type,
                pr_url=pr_url,
                success_count=1 if success else 0
            ))
        db.commit()
        db.close()

    def search(self, problem: str, k: int = 3):
        return self.store.similarity_search(problem, k=k)