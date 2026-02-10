# config.py

class Config:
    """
    Classe di configurazione centralizzata (Configuration Object).
    Raccoglie le costanti globali, gli iperparametri dei modelli AI e i percorsi di sistema.
    Permette un facile tuning delle performance senza modificare la logica del codice.
    """

    # --- SELEZIONE MODELLI AI (OLLAMA) ---
    # Modello Generativo (LLM): Llama 3.2 è scelto per il bilanciamento tra velocità e capacità di ragionamento.
    MODEL_NAME = 'llama3.2'
    # Modello di Embedding: Trasforma il testo in vettori per la ricerca semantica nel RAG (ChromaDB).
    EMBEDDING_MODEL = 'nomic-embed-text'

    # --- IPERPARAMETRI DI GENERAZIONE (TEMPERATURE) ---
    # Temperatura alta (0.7): Aumenta la varianza e la creatività.
    # Usata per: Generazione dello scenario, dialoghi dei personaggi (Roleplay), descrizioni narrative.
    TEMPERATURE_CREATIVA = 0.7

    # Temperatura bassa (0.1): Favorisce il determinismo e la precisione.
    # Usata per: Estrazione JSON, verifica logica (Fact-Checking), analisi forense.
    TEMPERATURE_LOGICA = 0.1

    # --- IMPOSTAZIONI RAG (Retrieval-Augmented Generation) ---
    # Prefisso per le collezioni nel database vettoriale per evitare collisioni tra NPC.
    RAG_COLLECTION_PREFIX = "investigazione_"
    # Top-K Retrieval: Numero massimo di "ricordi" (chunk) da recuperare per ogni query.
    # Tenuto basso (2) per evitare di inquinare il contesto con informazioni irrilevanti.
    MAX_RICORDI_RAG = 2

    # --- GESTIONE PERSISTENZA (FILE SYSTEM) ---
    # Directory dove verranno salvati i file JSON dello stato di gioco.
    SAVES_DIR = "salvataggi"
    EXTENSION = ".json"