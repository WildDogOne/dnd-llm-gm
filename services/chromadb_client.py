from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever
from haystack import Document
from haystack import Pipeline
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.preprocessors import DocumentPreprocessor, DocumentCleaner, DocumentSplitter
from haystack.components.converters import PyPDFToDocument
from haystack.components.writers import DocumentWriter
from core.settings import settings
from typing import List, Dict
from .ollama_client import ollama_client


class ChromadbClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ChromadbClient, cls).__new__(cls)
            cls._instance.__init__(*args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        self.document_store = ChromaDocumentStore(persist_path=settings.chromadb_folder)

    def get_document_count(self):
        return self.document_store.count_documents()

    def reset_store(self):
        if self.get_document_count() > 0:
            self.document_store.delete_all_documents()

    def embed(self, text: str, step) -> None:
        doc = Document(content=text)
        preproc = DocumentPreprocessor(split_by="word", split_length=10, split_overlap=0)
        preproc.warm_up()
        docs = preproc.run(documents=[doc])
        doc_embedder = SentenceTransformersDocumentEmbedder(
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
        doc_embedder.warm_up()
        docs_with_embeddings = doc_embedder.run(docs["documents"])
        self.document_store.write_documents(docs_with_embeddings["documents"])

    def retrieve(self, question: str, question_prompt: str = None) -> List[Dict]:

        text_embedder = SentenceTransformersTextEmbedder(
            model="sentence-transformers/all-MiniLM-L6-v2"
        )
        question_prompt = f"Formulate a question for a ChromaDB based on the following information, to retrieve more context. Only return the question: {question}"
        question = ollama_client.generate(question_prompt)

        retriever = ChromaEmbeddingRetriever(document_store=self.document_store)
        querying = Pipeline()
        querying.add_component("query_embedder", text_embedder)
        querying.add_component("retriever", retriever)
        querying.connect("query_embedder.embedding", "retriever.query_embedding")
        results = querying.run({"query_embedder": {"text": question}})
        outputs = []
        if results:
            for result in results["retriever"]["documents"]:
                outputs.append(result.content)
                if len(outputs) > 5:
                    break
        return outputs

    def embed_pdf(self, pdf):
        print(pdf)
        # converter = PyPDFToDocument()
        # docs = converter.run(sources=[pdf])
        pipeline = Pipeline()
        pipeline.add_component("converter", PyPDFToDocument())
        pipeline.add_component("cleaner", DocumentCleaner())
        pipeline.add_component("splitter", DocumentSplitter(split_by="sentence", split_length=5))
        pipeline.add_component("writer", DocumentWriter(document_store=self.document_store))
        pipeline.connect("converter", "cleaner")
        pipeline.connect("cleaner", "splitter")
        pipeline.connect("splitter", "writer")
        pipeline.run({"converter": {"sources": [str(pdf)]}})


chromadb_client = ChromadbClient()
