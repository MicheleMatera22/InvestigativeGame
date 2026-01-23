import ollama
import json

# --- CONFIGURAZIONE ---
MODELLO = 'llama3.2'


# --- 1. GENERATORE DI SCENARIO (ARCHITETTO) ---
def genera_scenario_con_ai():
    """
    Genera uno scenario COMPLESSO con:
    - 3 sospettati
    - Intro narrativa
    - Rapporto della scientifica (fatti oggettivi)
    """
    prompt_architetto = """
    Sei un game designer per un giallo investigativo.
    Genera un oggetto JSON valido.

    STRUTTURA JSON RICHIESTA:
    {
        "vittima": "Nome della vittima",
        "luogo_omicidio": "Luogo",
        "arma_reale": "Oggetto usato",
        "movente_reale": "Motivo",
        "intro_atmosfera": "Descrizione sensoriale (meteo, luci)",
        "rapporto_forense": [
            "Fatto oggettivo 1 (es. Orario del decesso)",
            "Fatto oggettivo 2 (es. Tracce trovate sulla scena)",
            "Fatto oggettivo 3 (es. Stato della vittima)"
        ],
        "sospettati": [
            {
                "id": 0, "nome": "Nome", "ruolo": "Ruolo", "colpevole": true, 
                "personalita": "Aggettivi", "alibi": "Alibi falso", "segreto": "Dettaglio incriminante"
            },
            {
                "id": 1, "nome": "Nome", "ruolo": "Ruolo", "colpevole": false,
                "personalita": "Aggettivi", "alibi": "Alibi vero", "segreto": "Segreto non criminale"
            },
            {
                "id": 2, "nome": "Nome", "ruolo": "Ruolo", "colpevole": false,
                "personalita": "Aggettivi", "alibi": "Alibi vero", "segreto": "Sospetto su altri"
            }
        ]
    }
    Importante: Il 'rapporto_forense' deve contenere indizi fisici reali (es. impronte, DNA, orari) che potrebbero smentire i sospettati.
    Rispondi SOLO con il JSON.
    """

    print("Creazione del caso in corso...")

    for i in range(3):
        try:
            response = ollama.chat(
                model=MODELLO,
                messages=[{'role': 'user', 'content': prompt_architetto}],
                format='json',
                options={'temperature': 0.8}
            )
            data = json.loads(response['message']['content'])
            if "sospettati" in data and "rapporto_forense" in data:
                return data
        except Exception as e:
            print(f"Tentativo {i + 1} fallito: {e}")

    return None


def generateIntro(data):
    """Genera l'intro narrativa"""
    user_prompt = f"""
    Scrivi una breve intro noir (max 5 righe) per questo caso.
    Luogo: {data['luogo_omicidio']}. Vittima: {data['vittima']}.
    Atmosfera: {data['intro_atmosfera']}.
    """
    response = ollama.chat(model=MODELLO, messages=[{'role': 'user', 'content': user_prompt}])
    return response['message']['content']


# --- 2. SISTEMA DI INTERROGATORIO (ATTORE) ---
def costruisci_prompt_sistema(sospettato, caso):
    base = f"Tu sei {sospettato['nome']}, {sospettato['ruolo']}.\n"
    if sospettato['colpevole']:
        obiettivi = f"SEI IL COLPEVOLE. Hai ucciso per {caso['movente_reale']}. Il tuo alibi è FALSO ({sospettato['alibi']}). Menti per proteggerti."
    else:
        obiettivi = f"SEI INNOCENTE. Il tuo alibi è VERO ({sospettato['alibi']}). Hai un segreto ({sospettato['segreto']}) ma non c'entra con l'omicidio."

    return base + obiettivi + "\nRispondi brevemente in prima persona."


def avvia_interrogatorio(sospettato, caso):
    """Gestisce il loop di chat con un singolo sospettato"""
    print(f"\n--- INIZIO INTERROGATORIO: {sospettato['nome']} ({sospettato['ruolo']}) ---")
    print("Digita 'FINE' per terminare e analizzare il sospetto.\n")

    # Memoria della chat
    system_prompt = costruisci_prompt_sistema(sospettato, caso)
    history = [{'role': 'system', 'content': system_prompt}]

    chat_transcript = []  # Salviamo solo il testo per l'analisi finale

    while True:
        user_input = input("DETECTIVE: ")
        if user_input.strip().upper() == 'FINE':
            break

        history.append({'role': 'user', 'content': user_input})
        chat_transcript.append(f"Detective: {user_input}")

        # Genera risposta
        print(f"{sospettato['nome']} sta pensando...")
        res = ollama.chat(model=MODELLO, messages=history)
        ai_reply = res['message']['content']

        print(f"{sospettato['nome'].upper()}: {ai_reply}")

        history.append({'role': 'assistant', 'content': ai_reply})
        chat_transcript.append(f"Sospettato: {ai_reply}")

    return chat_transcript


# --- 3. SISTEMA DI VALUTAZIONE (PROFILER) ---
def analizza_sospettato(chat_log, caso):
    """
    Confronta la chat con il rapporto forense e calcola la % di sospetto.
    """
    print("\n--- ANALISI DEL PROFILER AI IN CORSO... ---")

    # Uniamo i fatti del rapporto in una stringa
    report_str = "\n".join(f"- {f}" for f in caso['rapporto_forense'])
    chat_str = "\n".join(chat_log)

    prompt_profiler = f"""
    Sei un analista dell'FBI. Valuta il livello di sospetto di questo soggetto.

    FATTI OGGETTIVI (SCIENTIFICA):
    {report_str}

    TRASCRIZIONE INTERROGATORIO:
    {chat_str}

    COMPITO:
    1. Il sospettato si è contraddetto rispetto ai fatti oggettivi?
    2. È stato evasivo o difensivo?
    3. Assegna una percentuale di colpevolezza (0-100%).

    Rispondi SOLO con un JSON in questo formato:
    {{
        "percentuale": 0,
        "motivazione": "Spiegazione in due frasi."
    }}
    """

    try:
        response = ollama.chat(
            model=MODELLO,
            messages=[{'role': 'user', 'content': prompt_profiler}],
            format='json',
            options={'temperature': 0.1}  # Bassa temperatura per essere precisi
        )
        return json.loads(response['message']['content'])
    except Exception as e:
        return {"percentuale": 0, "motivazione": f"Errore analisi: {e}"}


# --- ESECUZIONE PRINCIPALE (MAIN LOOP) ---
def main():
    # 1. Generazione
    scenario = genera_scenario_con_ai()
    if not scenario:
        print("Errore fatale generazione scenario.")
        return

    print("\n" + "=" * 40)
    print(f"CASO: {generateIntro(scenario)}")
    print("=" * 40)

    # Mostriamo il Rapporto della Polizia al giocatore
    print("\n[RAPPORTO DELLA SCIENTIFICA]")
    for fatto in scenario['rapporto_forense']:
        print(f" - {fatto}")

    while True:
        print("\nCHI VUOI INTERROGARE?")
        for s in scenario['sospettati']:
            print(f"{s['id']}. {s['nome']} ({s['ruolo']})")
        print("X. Esci dal gioco")

        scelta = input("> ")
        if scelta.upper() == 'X': break

        try:
            # Trova il sospettato scelto
            sosp_id = int(scelta)
            sospettato_corrente = next(s for s in scenario['sospettati'] if s['id'] == sosp_id)

            # 2. Avvia Interrogatorio
            trascrizione = avvia_interrogatorio(sospettato_corrente, scenario)

            # 3. Analisi Finale (Profiler)
            if trascrizione:
                risultato = analizza_sospettato(trascrizione, scenario)

                print(f"\n--- RISULTATO ANALISI: {sospettato_corrente['nome']} ---")

                # Visualizzazione grafica barra
                punteggio = risultato['percentuale']
                bar = "█" * (punteggio // 10) + "░" * ((100 - punteggio) // 10)

                colore = "ALTO" if punteggio > 70 else "MEDIO" if punteggio > 40 else "BASSO"

                print(f"LIVELLO SOSPETTO: {punteggio}% [{colore}]")
                print(f"BARRA: [{bar}]")
                print(f"MOTIVAZIONE: {risultato['motivazione']}")

                if sospettato_corrente['colpevole']:
                    print("(NOTA DEBUG: Questo era il vero colpevole!)")

        except (ValueError, StopIteration):
            print("Scelta non valida.")


if __name__ == "__main__":
    main()