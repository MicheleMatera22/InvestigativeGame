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
    def __init__(self):
        self.scenario = None  # Conterrà i dati dello scenario (dict)
        self.kg = None  # Istanza del Knowledge Graph
        self.memorie = {}  # Dizionario {id_sospettato: istanza_MemoriaRAG}

        if not os.path.exists(Config.SAVES_DIR):
            os.makedirs(Config.SAVES_DIR)

    def genera_nuova_partita(self):
        """Genera lo scenario usando il Template Prompting"""
        print("Generazione Scenario in corso...")

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

        for _ in range(3):
            try:
                res = ollama.chat(
                    model=Config.MODEL_NAME,
                    messages=[{'role': 'user', 'content': prompt}],
                    format='json',
                    options={'temperature': Config.TEMPERATURE_CREATIVA}
                )
                # Validazione e conversione
                obj = ScenarioInvestigativo.model_validate_json(res['message']['content'])
                self.inizializza_dati(obj.model_dump())
                return True
            except ValidationError as e:
                print(f"Errore validazione: {e}")
            except Exception as e:
                print(f"Errore generazione: {e}")
        return False

    def genera_intro_narrativa(self):
        """Genera un prologo narrativo senza fare spoiler"""
        if not self.scenario:
            return "Nessuno scenario caricato."

        # 1. Selezioniamo SOLO i dati sicuri (Pubblici)
        # Non passiamo i sospettati o il colpevole per evitare spoiler accidentali
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
                options={'temperature': Config.TEMPERATURE_CREATIVA}  # Usiamo creatività alta qui
            )
            return res['message']['content']
        except Exception as e:
            return f"Errore generazione intro: {e}"

    def inizializza_dati(self, scenario_dict):
        """Costruisce Grafo e RAG partendo dai dati grezzi"""
        self.scenario = scenario_dict

        # 1. Costruisci Grafo (Knowledge Graph)
        self.kg = KnowledgeGraph()
        self.kg.costruisci_da_scenario(self.scenario)

        # 2. Inizializza Memorie RAG per ogni sospettato
        self.memorie = {}
        for s in self.scenario['sospettati']:
            mem = MemoriaRAG(collection_name=f"{Config.RAG_COLLECTION_PREFIX}{s['id']}")
            # Inseriamo i fatti forensi nella memoria a lungo termine
            for fatto in self.scenario['rapporto_forense']:
                mem.aggiungi_memoria(fatto, {"tipo": "forense"})
            self.memorie[s['id']] = mem

    def elabora_turno(self, id_sospettato, user_input, history_locale):
        """Gestisce un singolo scambio Botta e Risposta con RAG + Fact Checker"""
        sospettato = next(s for s in self.scenario['sospettati'] if s['id'] == id_sospettato)
        memoria = self.memorie[id_sospettato]

        # A. RAG Retrieval
        ricordi = memoria.recupera_contesto(user_input, n_results=Config.MAX_RICORDI_RAG)
        context_rag = "\n".join([f"- {r}" for r in ricordi])

        # B. Prompt Building
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

        # C. Generazione + Fact Checking (Neuro-Simbolico)
        risposta = self._genera_verificata(sospettato, user_input, messages)

        # D. Salvataggio Memoria
        memoria.aggiungi_memoria(f"D: {user_input} R: {risposta}", {"role": "chat"})

        return risposta

    def _costruisci_system_prompt(self, s):
        # 1. Definiamo lo stile linguistico basato sulla personalità
        prompt_stile = f"""
        Tuo Stile di Parlata: Basati sulla tua personalità '{s['personalita']}'.
        - Se sei 'Nervoso': usa frasi spezzate, balbetta ogni tanto (...), ripeti i concetti.
        - Se sei 'Arrogante': usa un tono superiore, frasi brevi, sii scocciato.
        - Se sei 'Calmo/Freddo': parla in modo lento, analitico e distaccato.
        - Se sei 'Amichevole': sii verboso, cerca di ingraziarti il detective.
        """

        # 2. Definiamo la psicologia profonda (Colpevole vs Innocente)
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

        # 3. Assemblaggio del Prompt Finale
        full_instruction = f"""
        [CONTESTO: GIOCO DI RUOLO NOIR]
        Sei {s['nome']}, {s['ruolo']}.

        {prompt_stile}

        {psicologia}

        IMPORTANTE: Rispondi SOLO come il personaggio. Non usare frasi come "Come modello AI...".
        """

        return full_instruction

    def _genera_verificata(self, sospettato, input_utente, messages):
        """Logica Neuro-Simbolica privata (Versione Anti-Rifiuto)"""
        # 1. Generazione Iniziale
        res = ollama.chat(model=Config.MODEL_NAME, messages=messages)
        testo_iniziale = res['message']['content']

        # 2. Verifica col Grafo
        fatti = self.kg.ottieni_fatti_su(sospettato['nome'])
        if not fatti:
            return testo_iniziale

        # Prompt di controllo
        check_prompt = f"""
        Fatti della Trama: {" | ".join(fatti)}
        Battuta del Personaggio: "{testo_iniziale}"

        La battuta contraddice i fatti della trama? Rispondi SI/NO.
        """
        check = ollama.chat(model=Config.MODEL_NAME, messages=[{'role': 'user', 'content': check_prompt}])

        # 3. Logica di Correzione
        if "SI" in check['message']['content'].upper():

            history_correzione = messages.copy()

            # Istruzione rinforzata per il Roleplay
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

            res_corretta = ollama.chat(model=Config.MODEL_NAME, messages=history_correzione)
            testo_corretto = res_corretta['message']['content']

            indicatori_ai = ["mi dispiace", "i'm sorry", "non posso", "language model", "modello linguistico"]
            if any(x in testo_corretto.lower() for x in indicatori_ai):
                return testo_iniziale  # Fallback alla prima risposta

            return testo_corretto

        return testo_iniziale

        # --- NUOVO SISTEMA DI SALVATAGGIO MULTIPLO ---

    def elenca_salvataggi(self):
            """Restituisce una lista ordinata dei file di salvataggio disponibili"""
            if not os.path.exists(Config.SAVES_DIR):
                return []

            try:
                # Prende solo i file che finiscono con l'estensione giusta (es. .json)
                files = [f for f in os.listdir(Config.SAVES_DIR) if f.endswith(Config.EXTENSION)]
                # Li ordina per ultima modifica (i più recenti per primi)
                files.sort(key=lambda x: os.path.getmtime(os.path.join(Config.SAVES_DIR, x)), reverse=True)
                return files
            except Exception as e:
                print(f"Errore lettura cartella: {e}")
                return []

    def salva_partita(self, nome_custom=None):
            """
            Salva la partita.
            Se nome_custom è vuoto, genera un nome basato su data e ora.
            """
            if not self.scenario:
                return "Errore: Nessuna partita attiva da salvare."

            if nome_custom:
                # Pulisce il nome da spazi e caratteri strani
                safe_name = "".join([c for c in nome_custom if c.isalnum() or c in (' ', '_', '-')]).strip()
                filename = f"{safe_name}{Config.EXTENSION}"
            else:
                # Genera nome automatico: caso_2023-10-27_15-30.json
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
            """Carica uno specifico file dalla cartella salvataggi"""
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
            Analizza la chat appena conclusa e confronta le dichiarazioni con i fatti noti (Knowledge Graph).
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