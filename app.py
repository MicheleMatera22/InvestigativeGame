import ollama
import json


# --- VARIABILI GLOBALI ---
scenario_dati = {}
conversation_history = []


def genera_scenario_con_ai():
    """
    Genera un SINGOLO scenario di omicidio (1 colpevole).
    """
    prompt_architetto = """
    Sei un generatore di dati per un gioco investigativo.
    Devi generare un singolo oggetto JSON valido che descrive un omicidio.

    Usa ESATTAMENTE questa struttura e queste chiavi:
    {
        "ruolo": "il ruolo del colpevole (es. Il Giardiniere)",
        "nome": "nome del colpevole",
        "vittima": "chi è stato ucciso",
        "luogo_omicidio": "dove è successo",
        "arma": "l'oggetto usato",
        "movente": "il motivo dell'omicidio",
        "alibi_falso": "una bugia su dove si trovava",
        "indizio_chiave": "un oggetto che lo incastra"
    }

    Inventa una storia noir. Rispondi SOLO con il JSON.
    """

    print("--- ARCHITETTO: Generazione scenario... ---")

    for i in range(3):  # 3 tentativi
        try:
            response = ollama.chat(
                model='llama3.2',
                messages=[{'role': 'user', 'content': prompt_architetto}],
                format='json',
                options={'temperature': 0.8}
            )
            data = json.loads(response['message']['content'])
            if "ruolo" in data and "arma" in data:
                return data
        except Exception as e:
            print(f"Tentativo {i + 1} fallito: {e}")

    return None


import ollama
import json


def generateIntro(data):
    # Se data è un oggetto/dizionario, lo convertiamo in stringa formattata
    data_str = json.dumps(data, indent=2, ensure_ascii=False) if isinstance(data, dict) else str(data)

    system_prompt = "Sei un premiato scrittore di gialli, famoso per le descrizioni atmosferiche e la suspense."

    user_prompt = f"""
    Scrivi l'introduzione di una storia basandoti su questi dettagli del caso:
    {data_str}

    Requisiti:
    - Inizia descrivendo l'ambientazione sensoriale (meteo, luci, suoni).
    - Porta lentamente il lettore verso la scoperta del corpo.
    - Usa un tono serio e drammatico.
    - Includi i dettagli chiave forniti (luogo, ora, arma) integrandoli nella narrazione.
    """

    response = ollama.chat(model='llama3.2',
                           messages=[
                               {'role': 'system', 'content': system_prompt},
                               {'role': 'user', 'content': user_prompt}
                           ],
                           options={'temperature': 0.7})

    return response['message']['content']

def costruisci_prompt_sistema(scenario):
    """Costruisce la personalità dell'AI Attore"""
    return f"""
    Tu sei {scenario['nome']}, {scenario['ruolo']}.
    Sei colpevole dell'omicidio di {scenario['vittima']}.
    Luogo: {scenario['luogo_omicidio']}.
    Arma reale: {scenario['arma']}.
    Movente reale: {scenario['movente']}.

    Il tuo alibi (falso) è: {scenario['alibi_falso']}.
    L'indizio che ti incastra è: {scenario['indizio_chiave']}.

    REGOLE:
    1. L'utente è un detective. Cerca di sembrare innocente.
    2. Rispondi in italiano, sii conciso.
    3. Non confessare mai spontaneamente.
    """

print(generateIntro(genera_scenario_con_ai()))