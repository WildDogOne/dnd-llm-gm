import chromadb
from chromadb.config import Settings
from core.settings import settings


class ChromadbClient:
    def __init__(self) -> None:
        self.path = settings.chromadb_folder
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=self.path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

    def get_document_count(self):
        # Create or get collection of your documents
        collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "Company knowledge base"}
        )

        print(f"Collection created with {collection.count()} documents")
chromadb_client = ChromadbClient()