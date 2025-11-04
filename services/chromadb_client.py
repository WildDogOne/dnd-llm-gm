import chromadb
from chromadb.config import Settings
from core.settings import settings
from typing import List, Dict
from .ollama_client import ollama_client


class ChromadbClient:
    def __init__(self) -> None:
        self.path = settings.chromadb_folder
        self.chunk_size = 500
        self.chunk_overlap = 200
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=self.path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

    def get_document_count(self):
        collection = self.get_collection()
        print(f"We have {collection.count()} stored documents")

    def clear_collection(self):
        # Get the documents collection
        collection = self.get_collection()
        # Clear all documents from the collection
        collection.delete(where={"ids": {"$gte": 0}})
        print("Collection cleared")

    def get_collection(self, collection_name: str = "dnd"):
        collection = self.client.get_or_create_collection(name=collection_name,
                                                          metadata={"description": "DnD Story History"})
        return collection

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks for better context"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            # Find natural break point
            if end < len(text):
                last_period = chunk.rfind('.')
                if last_period > start + 500:  # Ensure minimum chunk size
                    end = start + last_period + 1
                    chunk = text[start:end]

            chunks.append(chunk.strip())
            start = end - self.chunk_overlap

        return chunks

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings using Ollama"""
        embeddings = []

        for text in texts:
            embedding = ollama_client.embed(text)
            if isinstance(embedding, list) and len(embedding) == 1 and isinstance(embedding[0], list):
                embedding = embedding[0]

            embeddings.append(embedding)

        return embeddings

    def embed(self, text: str, step) -> None:
        chunks = self.chunk_text(text)
        embeddings = self.generate_embeddings(chunks)

        # Prepare data for ChromaDB
        collection = self.get_collection(collection_name="dnd")

        # Get the highest ID from the existing documents
        existing_ids = collection.get()
        if existing_ids['ids']:
            highest_id = max(existing_ids['ids'])
        else:
            highest_id = 0

        # Generate new IDs starting from the highest ID + 1
        ids = [f"{int(highest_id) + i + 1}" for i in range(len(chunks))]

        metadatas = [
            {
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        # Add to collection
        collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        self.get_document_count()
        #print(collection.get())

    def retrieve(self, question: str) -> List[Dict]:
        question_prompt = f"Formulate a question for a ChromaDB based on the following information, to retrieve more context: {question}"
        print(f"Question: {question_prompt}")
        # generate an embedding for the input and retrieve the most relevant doc
        embeddings = ollama_client.embed(inputs=question_prompt)
        collection = self.get_collection(collection_name="dnd")
        results = collection.query(
            query_embeddings=embeddings,
            n_results=1
        )
        data = results['documents'][0][0]
        print(f"Results: {data}")
        return data


chromadb_client = ChromadbClient()
