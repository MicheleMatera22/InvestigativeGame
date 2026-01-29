# AI Detective
> **Un sistema investigativo procedurale basato su LLM (Llama 3.2), RAG e Logic-Checking tramite Grafi.**

## 📖 Descrizione del Progetto

Questo progetto è un **motore di gioco investigativo testuale** che utilizza un approccio **Ibrido Neuro-Simbolico** per generare e gestire casi di omicidio procedurali.

A differenza dei comuni giochi basati su LLM (che soffrono di "allucinazioni" e incoerenze), questo sistema integra un **Knowledge Graph (Grafo della Conoscenza)** e un modulo **RAG (Retrieval-Augmented Generation)** per garantire che i personaggi mantengano coerenza logica, ricordino i fatti e non contraddicano la trama generata.

Il sistema è progettato per dimostrare come mitigare i limiti dei **Small Language Models (SLM)** come Llama 3.2 attraverso architetture software robuste.

---

## 🧠 Architettura del Sistema

Il software si basa su 4 moduli principali:

1.  **L'Architetto (Generative Layer):** Utilizza `Pydantic` per costringere l'LLM a generare scenari strutturati (JSON) perfettamente validi, creando vittime, luoghi, prove e sospettati unici ad ogni avvio.
2.  **La Memoria (RAG Layer):** Utilizza `ChromaDB` per memorizzare a lungo termine i rapporti forensi e la cronologia degli interrogatori, permettendo ai sospettati di ricordare dettagli detti in precedenza.
3.  **Il Giudice (Logic Layer):** Un modulo **Neuro-Simbolico** basato su `NetworkX`. Ogni volta che un sospettato risponde, il sistema verifica "silenziosamente" la risposta contro il Grafo dei Fatti. Se l'AI allucina (es. sbaglia un alibi), il sistema la corregge automaticamente prima di mostrare l'output all'utente.
4.  **L'Attore (Roleplay Layer):** Un sistema di prompt engineering avanzato ("Framing") che permette ai modelli di interpretare colpevoli che mentono intenzionalmente, aggirando i filtri di sicurezza standard.

---

## 🚀 Installazione e Setup

### Prerequisiti
* **Python 3.10+** installato.
* **Ollama** installato e in esecuzione sul computer.

### 1. Clona la repository
```bash
git clone [https://github.com/tuo-username/neuro-symbolic-detective.git](https://github.com/tuo-username/neuro-symbolic-detective.git)
cd neuro-symbolic-detective

```

### 2. Prepara l'ambiente virtuale

```bash
python -m venv .venv
source .venv/bin/activate  # Su Windows: .venv\Scripts\activate

```

### 3. Installa le dipendenze

```bash
pip install -r requirements.txt

```

*(Assicurati che `requirements.txt` contenga: `ollama`, `pydantic`, `chromadb`, `networkx`, `matplotlib`)*

### 4. Scarica il Modello AI

Il progetto è ottimizzato per **Llama 3.2** (leggero e veloce).

```bash
ollama pull llama3.2

```

---

## 🎮 Come Giocare

Avvia il gioco con il comando:

```bash
python main.py

```

1. **Generazione:** Il sistema creerà un nuovo caso di omicidio (Vittima, Luogo, 3 Sospettati, Prove).
2. **Indagine:**
* Leggi il **Rapporto Forense**.
* Scegli un sospettato dalla lista basandoti sulla **Pista Iniziale** (Motivo del Fermo).
* Interrogalo in linguaggio naturale.


3. **Verifica:**
* Quando scrivi `FINE` durante un interrogatorio, un **Analista Forense AI** confronterà la chat con la verità oggettiva e ti dirà se il sospettato ha mentito.


4. **Risoluzione:**
* Quando pensi di aver capito, scegli l'opzione **[A] ACCUSA**.
* Il sistema rivelerà la **Ground Truth** (Verità Oggettiva) e ti dirà se hai arrestato il vero colpevole.



---

## 📂 Struttura del Codice

Il progetto segue un'architettura modulare per garantire la manutenibilità:

* `main.py`: **Entry Point**. Gestisce l'interfaccia utente (CLI), il loop di gioco e i menu.
* `GameEngine.py`: **Core Logic**. Gestisce lo stato del gioco, orchestra le chiamate a Ollama, gestisce il ciclo di correzione degli errori e la logica di gioco.
* `models.py`: **Data Layer**. Definizioni delle classi `Pydantic` per la validazione rigorosa dei dati JSON.
* `config.py`: **Configuration**. Centralizza le costanti (modello, temperature, percorsi file).
* `GestoreMemoria.py`: **RAG Module**. Wrapper per ChromaDB.
* `KnowledgeGraph.py`: **Graph Module**. Wrapper per NetworkX, costruisce la mappa delle relazioni e dei fatti veri.

---

---

## 📜 Licenza

Progetto sviluppato per scopi accademici/tesi di laurea.
Distribuito sotto licenza MIT.

---

*Powered by [Ollama](https://ollama.ai/) & [Llama 3.2*](https://www.google.com/search?q=https://ai.meta.com/llama/)

```

```
