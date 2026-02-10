# 🕵️‍♂️ Neuro-Symbolic AI Detective
### Sistema Investigativo Procedurale con Architettura Ibrida (LLM + Knowledge Graph)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Ollama](https://img.shields.io/badge/AI-Ollama%20Local-orange)
![License](https://img.shields.io/badge/License-MIT-green)
![Thesis](https://img.shields.io/badge/Context-Bachelor%20Thesis-purple)

> **Progetto di Tesi:** "Integrazione Neuro-Simbolica per la Coerenza Narrativa in Sistemi Investigativi Generati da LLM."

## 📖 Descrizione

Questo progetto implementa un **motore di gioco investigativo testuale** basato su un'architettura **Neuro-Simbolica**.
L'obiettivo è risolvere il problema delle "allucinazioni" nei Large Language Models (LLM) durante la generazione di storie a lungo termine.

Il sistema combina:
1.  **Componente Neurale (LLM - Llama 3.2):** Per la generazione creativa di dialoghi, descrizioni e scenari.
2.  **Componente Simbolica (Knowledge Graph - NetworkX):** Per mantenere la "Ground Truth" (Verità Oggettiva) e validare logicamente le risposte.
3.  **Memoria RAG (ChromaDB):** Per gestire la persistenza delle informazioni a lungo termine.

## ✨ Funzionalità Chiave

* **♾️ Generazione Procedurale:** Ogni partita crea un caso unico (Vittima, Colpevole, Movente, Indizi) usando *Template Prompting* e validazione *Pydantic*.
* **🧠 Architettura Neuro-Simbolica:** Un sistema di "Fact-Checking" intercetta le risposte dell'NPC. Se l'NPC contraddice i fatti del Grafo, un secondo agente AI corregge la risposta in tempo reale.
* **📚 Memoria RAG (Retrieval-Augmented Generation):** I sospettati "ricordano" ciò che è stato detto in precedenza grazie a un database vettoriale.
* **⚡ Narrazione Dinamica (Plot Twist):** Il sistema monitora i turni di gioco e inietta proceduralmente "Colpi di Scena" (Breaking News) che modificano il Grafo e la Memoria dei personaggi in tempo reale.
* **💾 Sistema di Salvataggio:** Gestione completa della persistenza (Salvataggio/Caricamento stato JSON).
* **📊 Logger Sperimentale:** (Opzionale) Registra metriche di latenza e interventi del correttore logico per analisi statistiche.

## 🛠️ Architettura del Sistema

Il flusso di un turno di gioco segue questo pipeline:

1.  **Input Utente:** Il detective fa una domanda.
2.  **RAG Retrieval:** Il sistema recupera i ricordi pertinenti dal Vector Store.
3.  **Prompt Engineering:** Costruzione dinamica del prompt (Persona + Contesto + Obiettivi).
4.  **Generazione LLM:** Llama 3.2 genera una risposta preliminare.
5.  **Logic Check (Simbolico):** La risposta viene confrontata con i nodi del **Knowledge Graph**.
6.  **Correzione (Feedback Loop):** Se viene rilevata un'allucinazione, il sistema rigenera la risposta forzando la coerenza.

## 🚀 Installazione e Setup

### Prerequisiti
* Python 3.10 o superiore.
* [Ollama](https://ollama.com/) installato e in esecuzione.

### 1. Clona il Repository
```bash
git clone [https://github.com/tuo-username/neuro-symbolic-detective.git](https://github.com/tuo-username/neuro-symbolic-detective.git)
cd neuro-symbolic-detective
