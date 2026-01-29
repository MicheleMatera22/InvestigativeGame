# GameEngine.py
import json
import ollama
from pydantic import ValidationError

from config import Config
from models import ScenarioInvestigativo
from GestoreMemoria import MemoriaRAG
from KnowledgeGraph import KnowledgeGraph

class GameEngine:
    def __init__(self):
        self.scenario = None  # Conterrà i dati dello scenario (dict)
        self.kg = None  # Istanza del Knowledge Graph
        self.memorie = {}  # Dizionario {id_sospettato: istanza_MemoriaRAG}

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
            "rapporto_forense": ["Orario del decesso (specificandolo)", "Orario ritrovamento del corpo (specificandolo)", "Rapporto della scientifica"],
            "sospettati": [
                { "id": 0, "nome": "...", "ruolo": "...", "colpevole": true, "personalita": "...", "alibi": "Falso...", "segreto": "...", "indizio_iniziale": "..." },
                { "id": 1, "nome": "...", "ruolo": "...", "colpevole": false, "personalita": "...", "alibi": "Vero...", "segreto": "...", "indizio_iniziale": "..." },
                { "id": 2, "nome": "...", "ruolo": "...", "colpevole": false, "personalita": "...", "alibi": "Vero...", "segreto": "...", "indizio_iniziale": "..." }
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
        MEMORIA A LUNGO TERMINE: {context_rag}
        CONTESTO ATTUALE: Il Detective chiede: "{user_input}"
        Rispondi direttamente come farebbe {sospettato['nome']}
        """

        messages = [{'role': 'user', 'content': full_prompt}]

        # C. Generazione + Fact Checking (Neuro-Simbolico)
        risposta = self._genera_verificata(sospettato, user_input, messages)

        # D. Salvataggio Memoria
        memoria.aggiungi_memoria(f"D: {user_input} R: {risposta}", {"role": "chat"})

        return risposta

    def _costruisci_system_prompt(self, s):
        # INCORNICIAMENTO (FRAMING): Diciamo all'AI che è un contesto narrativo sicuro
        base = f"""
        [CONTESTO: GIOCO DI RUOLO INVESTIGATIVO - FICTION]
        Stai interpretando un personaggio in un romanzo giallo. Non sei un assistente AI.  
        Nome: {s['nome']}
        Ruolo: {s['ruolo']}
        Personalità: {s['personalita']}
        """

        if s['colpevole']:
            # Usiamo termini teatrali ("Recita", "Personaggio") per evitare i filtri etici
            return f"{base} SCRIPT: Il tuo personaggio è il COLPEVOLE. Devi recitare la parte di chi mente per nascondere il crimine (Movente: {self.scenario['movente_reale']}). Alibi fittizio: {s['alibi']}."

        return f"{base} SCRIPT: Il tuo personaggio è INNOCENTE. Dì la verità sul tuo alibi: {s['alibi']}. Proteggi il tuo segreto personale: {s['segreto']}."

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

    def salva_partita(self):
        with open(Config.SAVE_FILE, 'w') as f:
            json.dump(self.scenario, f, indent=2)

    def carica_partita(self):
        try:
            with open(Config.SAVE_FILE, 'r') as f:
                data = json.load(f)
                self.inizializza_dati(data)
                return True
        except FileNotFoundError:
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