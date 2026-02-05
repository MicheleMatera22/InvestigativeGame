import time
from GameEngine import GameEngine


def main():
    engine = GameEngine()

    print("1. Nuova Indagine")
    print("2. Carica Salvataggio")
    scelta = input("> ")

    # --- GESTIONE MENU INIZIALE (MODIFICATO) ---
    if scelta == '2':
        # 1. Chiediamo all'engine la lista dei file
        saves = engine.elenca_salvataggi()

        if not saves:
            print("\nNessun salvataggio trovato nella cartella 'salvataggi'.")
            print("Avvio una nuova indagine automatica...")
            scelta = '1'
        else:
            print("\n--- SALVATAGGI DISPONIBILI ---")
            for i, file in enumerate(saves):
                print(f"{i + 1}. {file}")
            print("0. Indietro / Nuova Partita")

            try:
                idx = int(input("\nScegli il numero del file > "))
                if 1 <= idx <= len(saves):
                    filename_scelto = saves[idx - 1]
                    print(f"Caricamento di '{filename_scelto}'...")

                    if engine.carica_partita(filename_scelto):
                        print("Partita caricata con successo!")
                    else:
                        print("Errore critico nel caricamento del file.")
                        return
                else:
                    # Se l'utente preme 0 o un numero sbagliato, va a nuova partita
                    print("Scelta annullata. Avvio nuova indagine...")
                    scelta = '1'
            except ValueError:
                print("Input non valido. Avvio nuova indagine...")
                scelta = '1'

    if scelta == '1':
        if not engine.genera_nuova_partita():
            print("Errore critico generazione. Verifica che Ollama sia attivo.")
            return

    # --- INTRODUZIONE AL CASO ---
    scen = engine.scenario
    print(engine.genera_intro_narrativa())
    print("RAPPORTO FORENSE INIZIALE:")
    for f in scen['rapporto_forense']:
        print(f"- {f}")

    # --- LOOP PRINCIPALE DEL GIOCO ---
    while True:
        print("\n" + "=" * 50)
        print("--- LISTA SOSPETTATI & PISTE ---")
        for s in scen['sospettati']:
            print(f"[{s['id']}] {s['nome'].upper()} ({s['ruolo']})")
            print(f"    ► PISTA INIZIALE: {s['indizio_iniziale']}")
            print("-" * 40)

        print("S. Salva ed Esci")
        print("A. ACCUSA E RISOLVI IL CASO")
        print("=" * 50)

        inp = input("> ").upper().strip()

        # --- OPZIONE SALVATAGGIO (MODIFICATO) ---
        if inp == 'S':
            print("\nVuoi dare un nome al salvataggio? (Lascia vuoto per data/ora automatica)")
            nome_user = input("Nome salvataggio: ").strip()

            # Passiamo il nome (o None) all'engine
            msg = engine.salva_partita(nome_user if nome_user else None)

            print(msg)  # Stampa "Partita salvata in..."
            print("Arrivederci.")
            break

        # --- OPZIONE ACCUSA (FINE GIOCO) ---
        elif inp == 'A':
            print("\n" + "!" * 40)
            print("FASE FINALE: FORMULAZIONE ACCUSA")
            print("!" * 40)
            print("Chi ritieni sia il colpevole?")

            try:
                id_accusa = int(input("Inserisci ID del sospettato > "))

                # Recuperiamo i dati reali dal JSON (Ground Truth)
                sospettato_scelto = next((s for s in scen['sospettati'] if s['id'] == id_accusa), None)
                vero_colpevole = next(s for s in scen['sospettati'] if s['colpevole'])

                if not sospettato_scelto:
                    print("ID non valido.")
                    continue

                print(f"\nStai arrestando {sospettato_scelto['nome']}...")
                time.sleep(1.5)  # Suspense

                if sospettato_scelto['colpevole']:
                    print("\nACCUSA FONDATA! HAI RISOLTO IL CASO.")
                    print(f"L'assassino era davvero {vero_colpevole['nome']}.")
                else:
                    print(f"\nERRORE GIUDIZIARIO. {sospettato_scelto['nome']} è INNOCENTE.")
                    print(f"Il vero assassino era {vero_colpevole['nome']}.")

                # Rivelazione della Verità
                print("\n--- RAPPORTO CONCLUSIVO (GROUND TRUTH) ---")
                print(f"MOVENTE REALE: {scen['movente_reale']}")
                print(f"ARMA DEL DELITTO: {scen['arma_reale']}")
                print(f"ALIBI DEL COLPEVOLE: Era FALSO ({vero_colpevole['alibi']})")
                print(f"SEGRETO: {vero_colpevole['segreto']}")

                break  # Termina il programma

            except ValueError:
                print("Devi inserire un numero.")

        # --- OPZIONE INTERROGATORIO ---
        elif inp.isdigit():
            id_s = int(inp)
            if 0 <= id_s < 3:
                nome_sosp = scen['sospettati'][id_s]['nome']
                print(f"\n--- INIZIO INTERROGATORIO: {nome_sosp} ---")
                print(f"(Scrivi 'FINE' per terminare e ricevere il rapporto dell'Analista)")

                history = []
                while True:
                    d = input("DETECTIVE: ")

                    # --- GENERAZIONE RAPPORTO POLIZIA ---
                    if d.upper() == 'FINE':
                        if not history:
                            print("Non hai fatto domande. Nessun rapporto generato.")
                            break

                        print("\n" + "." * 50)
                        print("La polizia sta esaminando la trascrizione dell'interrogatorio...")

                        # Chiamata alla nuova funzione in GameEngine
                        rapporto = engine.genera_rapporto_polizia(id_s, history)

                        print("\n--- RAPPORTO PRELIMINARE DI POLIZIA ---")
                        print(f"SOGGETTO: {nome_sosp.upper()}")
                        print("-" * 40)
                        print(rapporto)
                        print("-" * 40)
                        input("(Premi Invio per tornare al menu principale)")
                        break

                    # --- TURNO DI DIALOGO STANDARD ---
                    r = engine.elabora_turno(id_s, d, history)
                    print(f"SOSPETTATO: {r}")
                    history.append(f"D: {d} R: {r}")


if __name__ == "__main__":
    main()