# config.py

class Config:
    # Modelli AI
    MODEL_NAME = 'llama3.2'
    EMBEDDING_MODEL = 'nomic-embed-text'

    # Parametri Generazione
    TEMPERATURE_CREATIVA = 0.7  # Per generare lo scenario
    TEMPERATURE_LOGICA = 0.1  # Per il fact-checking e profiler

    # Impostazioni RAG
    RAG_COLLECTION_PREFIX = "investigazione_"
    MAX_RICORDI_RAG = 2

    # File
    SAVE_FILE = "salvataggio_partita.json"