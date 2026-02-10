# GameEngine.py
import json
import ollama
from pydantic import ValidationError
import os
from datetime import datetime
from config import Config
from models import ScenarioInvestigativo
from GestoreMemoria import MemoriaRAG
from KnowledgeGraph import KnowledgeGraph


class GameEngine:
    """
    Classe principale (Controller) che orchestra l'intera logica del sistema investigativo.
    Responsabilità principali:
    1. Generazione Procedurale: Creazione di scenari unici tramite LLM e validazione strutturale.
    2. Gestione della Memoria: Coordinamento tra Memoria a Breve Termine (Chat History) e a Lungo Termine (RAG).
    3. Verifica Neuro-Simbolica: Mitigazione delle allucinazioni confrontando l'output dell'LLM con il Knowledge Graph.
    4. Gestione del Flusso: Turni, salvataggi e colpi di scena dinamici.
    """

    def __init__(self):
        # Inizializzazione dello stato del gioco
        self.scenario = None  # Dizionario contenente i dati strutturati della partita corrente
        self.kg = None  # Istanza del Knowledge Graph (Verità Oggettiva / Ground Truth)
        self.memorie = {}  # Dizionario che mappa ID sospettato -> Istanza MemoriaRAG (Vector Store)

        # Variabili per la gestione della progressione temporale e narrativa
        self.turni_giocati = 0
        self.evento_avvenuto = False  # Flag per garantire che il colpo di scena avvenga una sola volta

        # Verifica e creazione della directory per la persistenza dei dati
        if not os.path.exists(Config.SAVES_DIR):
            os.makedirs(Config.SAVES_DIR)

    def genera_nuova_partita(self):
        """
        Genera un nuovo scenario investigativo completo utilizzando la tecnica del 'Template Prompting'.
        Costringe l'LLM a produrre un output JSON conforme allo schema Pydantic 'ScenarioInvestigativo'.
        Include un meccanismo di 'Self-Correction' (fino a 3 tentativi) in caso di JSON malformato.
        """
        print("Generazione Scenario in corso...")

        # Prompt Engineering: Definizione rigorosa della struttura dati attesa
        prompt = """
        Sei un game designer di gialli procedurali.
        Genera un JSON seguendo ESATTAMENTE questa struttura:
        {
            "vittima": "Nome Cognome",
            "luogo_omicidio": "Descrizione noir",
            "arma_reale": "Oggetto",
            "movente_reale": "Motivo",
            "intro_atmosfera": "Meteo e luci",
            "rapporto_forense": ["Specifica solo l'ora del decesso", "Specifica solo l'ora del ritrovamento del corpo", "Rapporto della scientifica"],
            "sospettati": [
                { "id": 0, "nome": "...", "ruolo": "...", "colpevole": true, "personalita": ""personalita": "Aggettivo forte che definisce come parla (es. Balbuziente, Arrogante, Logorroico, Timido)",", "alibi": "Falso...", "segreto": "...", "indizio_iniziale": "..." },
                { "id": 1, "nome": "...", "ruolo": "...", "colpevole": false, "personalita": ""personalita": "Aggettivo forte che definisce come parla (es. Balbuziente, Arrogante, Logorroico, Timido)",", "alibi": "Vero...", "segreto": "...", "indizio_iniziale": "..." },
                { "id": 2, "nome": "...", "ruolo": "...", "colpevole": false, "personalita": ""personalita": "Aggettivo forte che definisce come parla (es. Balbuziente, Arrogante, Logorroico, Timido)",", "alibi": "Vero...", "segreto": "...", "indizio_iniziale": "..." }
            ]
        }
        Rispondi SOLO col JSON.
        IMPORTANTE: 
        - Assicurati di chiudere tutte le parentesi graffe e quadre. Usa doppi apici.
        - L'indizio_iniziale deve dare al detective un motivo valido per sospettare di loro.
        REGOLE:
        - I nomi dei sospettati devono essere TUTTI diversi tra loro e DIVERSI dalla vittima.
        - Usa nomi e cognomi inglesi vari.
        """

        # Ciclo di retry per gestire eventuali errori di generazione del JSON
        for _ in range(3):
            try:
                # Chiamata all'LLM locale (Ollama)
                res = ollama.chat(
                    model=Config.MODEL_NAME,
                    messages=[{'role': 'user', 'content': prompt}],
                    format='json',  # Forza la modalità JSON di Llama
                    options={'temperature': Config.TEMPERATURE_CREATIVA}
                )
                # Validazione dei dati tramite Pydantic: se il JSON non rispetta lo schema, solleva ValidationError
                obj = ScenarioInvestigativo.model_validate_json(res['message']['content'])
                # Inizializzazione delle strutture dati di gioco
                self.inizializza_dati(obj.model_dump())
                return True
            except ValidationError as e:
                print(f"Errore validazione: {e}")
            except Exception as e:
                print(f"Errore generazione: {e}")
        return False

    def genera_intro_narrativa(self):
        """
        Genera un prologo narrativo ("Flavor Text") basato sui dati generati.
        IMPORTANTE: Questa funzione filtra i dati passati all'LLM (escludendo colpevole e movente)
        per evitare che il modello generi spoiler accidentali nell'introduzione.
        """
        if not self.scenario:
            return "Nessuno scenario caricato."

        # 1. Selezione dei soli dati pubblici (Data Privacy interna al prompt)
        dati_sicuri = f"""
        VITTIMA: {self.scenario['vittima']}
        LUOGO: {self.scenario['luogo_omicidio']}
        ATMOSFERA: {self.scenario['intro_atmosfera']}
        FATTI NOTI: {", ".join(self.scenario['rapporto_forense'])}
        """

        prompt = f"""
        Sei un narratore di romanzi Gialli.
        Scrivi un BREVE prologo introduttivo per iniziare la storia.

        Usa questi elementi:
        {dati_sicuri}

        REGOLE:
        1. Usa un tono cupo, misterioso e coinvolgente.
        2. NON menzionare mai chi è il colpevole.
        3. NON elencare i fatti come una lista, ma trasformali in narrazione descrittiva.
        """

        try:
            res = ollama.chat(
                model=Config.MODEL_NAME,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': Config.TEMPERATURE_CREATIVA}  # Alta temperatura per maggiore creatività
            )
            return res['message']['content']
        except Exception as e:
            return f"Errore generazione intro: {e}"

    def inizializza_dati(self, scenario_dict):
        """
        Setup dell'ambiente di gioco (Environment Setup).
        Trasforma i dati grezzi JSON in strutture semantiche interrogabili (Grafo e Vector Store).
        """
        self.scenario = scenario_dict
        # Ripristino dello stato dei contatori (utile nel caricamento partite)
        self.turni_giocati = scenario_dict.get('turni_giocati', 0)
        self.evento_avvenuto = scenario_dict.get('evento_avvenuto', False)

        # 1. Costruzione del Knowledge Graph (Componente Simbolica)
        # Mappa le relazioni statiche tra sospettati, vittima e luoghi
        self.kg = KnowledgeGraph()
        self.kg.costruisci_da_scenario(self.scenario)

        # Se stiamo caricando una partita dove è già avvenuto un evento dinamico, aggiorniamo il grafo
        if self.evento_avvenuto and 'evento_testo' in self.scenario:
            self.kg.aggiungi_fatto(self.scenario['evento_testo'])

        # 2. Inizializzazione RAG (Retrieval-Augmented Generation)
        # Crea una collezione vettoriale separata per ogni sospettato
        self.memorie = {}
        for s in self.scenario['sospettati']:
            # Inizializza ChromaDB per questo specifico NPC
            mem = MemoriaRAG(collection_name=f"{Config.RAG_COLLECTION_PREFIX}{s['id']}")

            # Popolamento memoria a lungo termine con i fatti forensi noti
            for fatto in self.scenario['rapporto_forense']:
                mem.aggiungi_memoria(fatto, {"tipo": "forense"})

            # Aggiornamento memoria se presente un evento dinamico pregresso
            if self.evento_avvenuto and 'evento_testo' in self.scenario:
                mem.aggiungi_memoria(self.scenario['evento_testo'], {"tipo": "breaking_news"})
            self.memorie[s['id']] = mem

    def elabora_turno(self, id_sospettato, user_input, history_locale):
        """
        Gestisce il ciclo principale di interazione (Game Loop).
        Esegue la pipeline RAG -> Prompt -> Generation -> Validation.
        """
        self.turni_giocati += 1
        sospettato = next(s for s in self.scenario['sospettati'] if s['id'] == id_sospettato)
        memoria = self.memorie[id_sospettato]

        # A. Retrieval (RAG): Recupera i chunk di memoria più rilevanti per la domanda attuale
        ricordi = memoria.recupera_contesto(user_input, n_results=Config.MAX_RICORDI_RAG)
        context_rag = "\n".join([f"- {r}" for r in ricordi])

        # B. Prompt Engineering: Costruzione dinamica del contesto per l'LLM
        sys = self._costruisci_system_prompt(sospettato)
        full_prompt = f"""
                {sys}

                [MEMORIA A LUNGO TERMINE (Cosa hai già detto)]: 
                {context_rag}

                [SITUAZIONE ATTUALE]:
                Il Detective ti sta interrogando. La tensione è alta.
                Domanda del Detective: "{user_input}"

                [TUA RISPOSTA]:
                (Ricorda il tuo stile: {sospettato['personalita']}. Usa il tic comportamentale (*) solo se stai mentendo o sei in panico).
                """

        messages = [{'role': 'user', 'content': full_prompt}]

        # C. Generazione Neuro-Simbolica: Generazione con controllo fattuale
        risposta = self._genera_verificata(sospettato, user_input, messages)

        # D. Aggiornamento Memoria: Salva lo scambio corrente nel database vettoriale
        memoria.aggiungi_memoria(f"D: {user_input} R: {risposta}", {"role": "chat"})

        return risposta

    def _costruisci_system_prompt(self, s):
        """
        Definisce la 'Persona' dell'agente.
        Utilizza tecniche di 'Role-Play Prompting' per definire:
        - Stile comunicativo.
        - Obiettivi nascosti (Mantenere l'alibi o nascondere segreti).
        - Comportamenti non verbali (Tic).
        """
        # 1. Configurazione dello stile linguistico
        prompt_stile = f"""
        Tuo Stile di Parlata: Basati sulla tua personalità '{s['personalita']}'.
        - Se sei 'Nervoso': usa frasi spezzate, balbetta ogni tanto (...), ripeti i concetti.
        - Se sei 'Arrogante': usa un tono superiore, frasi brevi, sii scocciato.
        - Se sei 'Calmo/Freddo': parla in modo lento, analitico e distaccato.
        - Se sei 'Amichevole': sii verboso, cerca di ingraziarti il detective.
        """

        # 2. Iniezione della logica comportamentale (Conditional Logic nel prompt)
        if s['colpevole']:
            psicologia = f"""
            [RUOLO: COLPEVOLE]
            Sei l'assassino. Il tuo obiettivo è NON farti scoprire, ma sei sotto stress.

            COME COMPORTARTI:
            1. MENTI sul tuo alibi ({s['alibi']}), ma fallo sembrare credibile.
            2. SVIA IL DISCORSO: Se il detective chiede dell'arma o del movente ({self.scenario['movente_reale']}), diventa vago, difensivo o accusa qualcun altro.
            3. INDIZIO SOTTILE (TELL): Quando menti spudoratamente, aggiungi un piccolo tic comportamentale tra asterischi (es. *si tocca il collo*, *evita lo sguardo*, *ride nervosamente*).
            4. Non confessare MAI direttamente.
            """
        else:
            psicologia = f"""
            [RUOLO: INNOCENTE]
            Non hai ucciso nessuno, ma hai un SEGRETO imbarazzante da nascondere: {s['segreto']}.

            COME COMPORTARTI:
            1. Dì la VERITÀ assoluta sul tuo alibi ({s['alibi']}). Vuoi che la polizia ti scagioni dall'omicidio.
            2. PROTEGGI IL SEGRETO: Se il detective fa domande che si avvicinano al tuo segreto ({s['segreto']}), diventa evasivo, nervoso o arrabbiato. NON rivelarlo a meno che non ti senta alle strette.
            3. Sii collaborativo sull'omicidio, ma reticente sulla tua vita privata.
            """

        # 3. Assemblaggio finale
        full_instruction = f"""
        [CONTESTO: GIOCO DI RUOLO NOIR]
        Sei {s['nome']}, {s['ruolo']}.

        {prompt_stile}

        {psicologia}

        IMPORTANTE: Rispondi SOLO come il personaggio. Non usare frasi come "Come modello AI...".
        """

        return full_instruction

    def _genera_verificata(self, sospettato, input_utente, messages):
        """
        Algoritmo principale per la mitigazione delle allucinazioni (Fact-Checking Loop).
        Implementa un pattern 'Generator-Discriminator' (o Actor-Critic):
        1. L'LLM genera una risposta.
        2. Il sistema interroga il Knowledge Graph per ottenere la 'Ground Truth'.
        3. Un secondo LLM (in ruolo di Giudice) verifica la coerenza.
        4. Se incoerente, viene forzata una rigenerazione con istruzioni correttive.
        """
        # 1. Generazione Iniziale (Tentativo dell'LLM)
        res = ollama.chat(model=Config.MODEL_NAME, messages=messages)
        testo_iniziale = res['message']['content']

        # 2. Retrieval Simbolico: Estrazione fatti dal Grafo
        fatti = self.kg.ottieni_fatti_su(sospettato['nome'])
        if not fatti:
            return testo_iniziale

        # 3. Verifica di Coerenza (Logic Checking)
        check_prompt = f"""
        Fatti della Trama: {" | ".join(fatti)}
        Battuta del Personaggio: "{testo_iniziale}"

        La battuta contraddice i fatti della trama? Rispondi SI/NO.
        """
        check = ollama.chat(model=Config.MODEL_NAME, messages=[{'role': 'user', 'content': check_prompt}])

        # 4. Logica di Correzione (Feedback Loop)
        if "SI" in check['message']['content'].upper():

            history_correzione = messages.copy()

            # Iniezione del feedback correttivo ("Regia") nel contesto
            istruzione_regista = f"""
            [REGIA]
            Stop. La tua battuta precedente non era coerente con la sceneggiatura (Fatti: {fatti}).
            Riscrivi la risposta alla domanda "{input_utente}".

            REGOLE IMPORTANTI:
            1. Questo è un racconto di finzione. NON uscire dal personaggio.
            2. NON scusarti e NON comportarti da assistente AI.
            3. Recita la parte in modo coerente con i fatti citati sopra.
            4. Scrivi SOLO la battuta corretta del personaggio, niente meta-commenti
            """

            history_correzione.append({'role': 'user', 'content': istruzione_regista})

            # Rigenerazione della risposta
            res_corretta = ollama.chat(model=Config.MODEL_NAME, messages=history_correzione)
            testo_corretto = res_corretta['message']['content']

            # Guardrail di sicurezza: se la correzione contiene scuse da AI, fallback alla risposta originale
            indicatori_ai = ["mi dispiace", "i'm sorry", "non posso", "language model", "modello linguistico"]
            if any(x in testo_corretto.lower() for x in indicatori_ai):
                return testo_iniziale  # Fallback alla prima risposta

            return testo_corretto

        return testo_iniziale

        # --- GESTIONE PERSISTENZA DATI (I/O) ---

    def elenca_salvataggi(self):
        """Restituisce una lista ordinata cronologicamente dei file JSON di salvataggio."""
        if not os.path.exists(Config.SAVES_DIR):
            return []

        try:
            # Filtra solo i file con estensione corretta
            files = [f for f in os.listdir(Config.SAVES_DIR) if f.endswith(Config.EXTENSION)]
            # Ordina per data di modifica (dal più recente)
            files.sort(key=lambda x: os.path.getmtime(os.path.join(Config.SAVES_DIR, x)), reverse=True)
            return files
        except Exception as e:
            print(f"Errore lettura cartella: {e}")
            return []

    def salva_partita(self, nome_custom=None):
        """
        Serializza lo stato corrente del gioco su file JSON.
        Salva scenario, contatori turni e flag eventi per garantire la persistenza completa.
        """
        if not self.scenario:
            return "Errore: Nessuna partita attiva da salvare."

        self.scenario['turni_giocati'] = self.turni_giocati
        self.scenario['evento_avvenuto'] = self.evento_avvenuto

        if nome_custom:
            # Sanitizzazione del nome file
            safe_name = "".join([c for c in nome_custom if c.isalnum() or c in (' ', '_', '-')]).strip()
            filename = f"{safe_name}{Config.EXTENSION}"
        else:
            # Generazione nome automatico con Timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"caso_{timestamp}{Config.EXTENSION}"

        filepath = os.path.join(Config.SAVES_DIR, filename)

        try:
            with open(filepath, 'w') as f:
                json.dump(self.scenario, f, indent=2)
            return f"Partita salvata con successo in: '{filename}'"
        except Exception as e:
            return f"Errore critico durante il salvataggio: {e}"

    def carica_partita(self, filename):
        """
        Deserializza il file JSON e ripristina lo stato del GameEngine.
        Richiama inizializza_dati() per ricostruire Grafo e RAG.
        """
        filepath = os.path.join(Config.SAVES_DIR, filename)

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Re-inizializza tutta la logica (Grafo, RAG, ecc.) con i dati caricati
                self.inizializza_dati(data)
                return True
        except FileNotFoundError:
            print(f"File non trovato: {filepath}")
            return False
        except Exception as e:
            print(f"Errore caricamento file corrotta: {e}")
            return False

    def genera_rapporto_polizia(self, id_sospettato, history_list):
        """
        Funzione di Analisi e Summarization.
        Usa l'LLM per confrontare la trascrizione dell'interrogatorio (History)
        con la Ground Truth (Knowledge Graph), evidenziando discrepanze.
        """
        if not history_list:
            return "Nessuna dichiarazione raccolta (Interrogatorio vuoto)."

        sospettato = next(s for s in self.scenario['sospettati'] if s['id'] == id_sospettato)

        # Recuperiamo la verità oggettiva dal Grafo
        fatti_reali = self.kg.ottieni_fatti_su(sospettato['nome'])
        fatti_str = " | ".join(fatti_reali) if fatti_reali else "Nessun fatto specifico noto."

        # Convertiamo la lista della chat in testo
        chat_str = "\n".join(history_list)

        prompt_analista = f"""
            Sei un Analista della Polizia. 
            Confronta le dichiarazioni del sospettato con i Fatti Accertati.

            SOSPETTATO: {sospettato['nome']}
            FATTI ACCERTATI (VERITÀ): {fatti_str}

            TRASCRIZIONE INTERROGATORIO:
            {chat_str}

            COMPITO:
            Scrivi un breve "Rapporto di Verifica" (max 3-4 righe).
            Per ogni punto chiave detto dal sospettato, scrivi se è "CONFERMATO" dai fatti o "SMENTITO" (contraddizione).
            Se il sospettato ha detto cose non verificabili, scrivi "NON VERIFICABILE".
            Usa un tono freddo e burocratico.
            """

        try:
            res = ollama.chat(model=Config.MODEL_NAME, messages=[{'role': 'user', 'content': prompt_analista}])
            return res['message']['content']
        except Exception as e:
            return f"Errore generazione rapporto: {e}"

    def verifica_colpo_scena(self):
        """
        Gestisce la Narrazione Dinamica (Dynamic Storytelling).
        Controlla il progresso del gioco (turni) e inietta proceduralmente nuovi fatti (nodi)
        nel Grafo e nella Memoria RAG, simulando l'evoluzione delle indagini in tempo reale.
        """
        SOGLIA_TURNI = 4  # Soglia di attivazione evento

        # Verifica se l'evento è già accaduto o se è troppo presto
        if self.evento_avvenuto or self.turni_giocati < SOGLIA_TURNI:
            return None

        print(">>> ENGINE: Generazione Colpo di Scena in corso...")

        # 1. Generazione Creativa del Colpo di Scena
        prompt = f"""
        Sei uno scrittore di thriller.
        Scenario: {self.scenario['vittima']} ucciso a {self.scenario['luogo_omicidio']}.

        Genera una "BREAKING NEWS" (un fatto nuovo improvviso) che complica le indagini.
        Esempi:
        - "È stata ritrovata l'arma del delitto in un bidone vicino."
        - "Un testimone anonimo afferma di aver visto un'auto rossa fuggire."
        - "L'autopsia rivela una traccia di veleno non notata prima."

        REGOLE:
        1. Max 1 frase.
        2. Deve essere un fatto concreto.
        3. NON rivelare il colpevole, ma aggiungi tensione.
        """

        try:
            res = ollama.chat(model=Config.MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
            nuovo_fatto = res['message']['content'].strip()

            # 2. Aggiornamento dello Stato del Gioco
            self.evento_avvenuto = True
            self.scenario['evento_testo'] = nuovo_fatto  # Persistenza nel JSON

            # 3. Aggiornamento Simbolico (Knowledge Graph)
            # Inserisce il nuovo fatto come nodo, rendendolo "verità" per il Fact-Checker
            self.kg.aggiungi_fatto(nuovo_fatto)

            # 4. Aggiornamento Semantico (RAG)
            # Propaga l'informazione a tutti gli agenti, simulando la diffusione della notizia
            for id_sosp, memoria in self.memorie.items():
                memoria.aggiungi_memoria(nuovo_fatto, {"tipo": "breaking_news"})

            return nuovo_fatto

        except Exception as e:
            print(f"Errore generazione evento: {e}")
            return None