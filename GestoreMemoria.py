import chromadb
import ollama
import uuid

class MemoriaRAG:
    def __init__(self, collection_name="investigazione"):
        # ChromaDB client effimero (resetta alla chiusura script)
        self.client = chromadb.Client()
        try:
            self.collection = self.client.get_or_create_collection(name=collection_name)
        except:
            self.client.delete_collection(collection_name)
            self.collection = self.client.create_collection(name=collection_name)

    def _get_embedding(self, text):
        # Richiede: ollama pull nomic-embed-text
        response = ollama.embeddings(model='nomic-embed-text', prompt=text)
        return response['embedding']

    def aggiungi_memoria(self, testo, metadati):
        vettore = self._get_embedding(testo)
        self.collection.add(
            documents=[testo],
            embeddings=[vettore],
            metadatas=[metadati],
            ids=[str(uuid.uuid4())]
        )

    def recupera_contesto(self, query, n_results=3):
        vettore = self._get_embedding(query)
        results = self.collection.query(
            query_embeddings=[vettore],
            n_results=n_results
        )
        if results['documents']:
            return results['documents'][0]
        return []