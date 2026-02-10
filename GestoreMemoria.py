import chromadb
import ollama
import uuid

class MemoriaRAG:
    """
    Gestisce la memoria a lungo termine dei personaggi usando RAG (Retrieval-Augmented Generation).
    Utilizza ChromaDB come database vettoriale per archiviare e recuperare frammenti di conversazione
    o fatti basati sulla similarità semantica.
    """
    def __init__(self, collection_name="investigazione"):
        # ChromaDB client effimero (resetta alla chiusura script)
        self.client = chromadb.Client()
        try:
            self.collection = self.client.get_or_create_collection(name=collection_name)
        except:
            self.client.delete_collection(collection_name)
            self.collection = self.client.create_collection(name=collection_name)

    def _get_embedding(self, text):
        """
        Genera l'embedding vettoriale per un testo usando il modello locale via Ollama.
        Richiede che il modello 'nomic-embed-text' sia installato (ollama pull nomic-embed-text).
        """
        # Richiede: ollama pull nomic-embed-text
        response = ollama.embeddings(model='nomic-embed-text', prompt=text)
        return response['embedding']

    def aggiungi_memoria(self, testo, metadati):
        """
        Archivia un nuovo ricordo nel database vettoriale.
        :param testo: Il contenuto testuale del ricordo (es. una frase detta).
        :param metadati: Dizionario con info extra (es. chi l'ha detto, timestamp, tipo).
        """
        vettore = self._get_embedding(testo)
        self.collection.add(
            documents=[testo],
            embeddings=[vettore],
            metadatas=[metadati],
            ids=[str(uuid.uuid4())]
        )

    def recupera_contesto(self, query, n_results=3):
        """
        Cerca i ricordi più rilevanti semanticamente rispetto alla query.
        :param query: La frase attuale o domanda per cui cercare contesto.
        :param n_results: Numero di frammenti da recuperare.
        """
        vettore = self._get_embedding(query)
        results = self.collection.query(
            query_embeddings=[vettore],
            n_results=n_results
        )
        if results['documents']:
            return results['documents'][0]
        return []