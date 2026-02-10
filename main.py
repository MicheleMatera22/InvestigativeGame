import time
from GameEngine import GameEngine


def main():
    """
    Funzione principale (Entry Point) dell'applicazione.
    Gestisce il ciclo di vita del gioco: inizializzazione, menu,
    loop di gioco principale e interazione utente.
    """

    # Inizializzazione del motore di gioco (GameEngine)
    # Questo carica le configurazioni e prepara le strutture dati (Grafo, RAG, ecc.)
    engine = GameEngine()

    # Stampa del menu iniziale
    print("1. Nuova Indagine")
    print("2. Carica Salvataggio")
    scelta = input("> ")

    # --- GESTIONE MENU INIZIALE ---
    # Logica per gestire il caricamento di una partita esistente
    if scelta == '2':
        # Recupera la lista dei file JSON dalla cartella dei salvataggi
        saves = engine.elenca_salvataggi()

        if not saves:
            # Se non ci sono salvataggi, notifica l'utente e passa alla creazione
            print("\nNessun salvataggio trovato.")
            print("Avvio nuova indagine...")
            scelta = '1'  # Fallback a nuova partita
        else:
            # Mostra l'elenco dei file disponibili
            print("\nSALVATAGGI DISPONIBILI")
            for i, file in enumerate(saves):
                print(f"{i + 1}. {file}")
            print("0. Indietro")

            try:
                # Gestione input selezione file
                idx = int(input("\nScegli file > "))
                if 1 <= idx <= len(saves):
                    filename_scelto = saves[idx - 1]
                    print(f"Caricamento di '{filename_scelto}'...")

                    # Tenta il caricamento dei dati (JSON -> Oggetti)
                    if engine.carica_partita(filename_scelto):
                        print("Partita caricata.")
                    else:
                        print("Errore nel caricamento.")
                        return
                else:
                    scelta = '1'  # Se scelta non valida o indietro, nuova partita
            except ValueError:
                scelta = '1'

    # --- GENERAZIONE NUOVA PARTITA ---
    # Se l'utente ha scelto '1' o se il caricamento è fallito/annullato
    if scelta == '1':
        # Chiama il metodo che usa l'LLM per generare proceduralmente lo scenario
        if not engine.genera_nuova_partita():
            print("Errore critico generazione.")
            return

    # --- INTRODUZIONE AL CASO ---
    # Recupera il dizionario dello scenario generato/caricato
    scen = engine.scenario

    # Rimosso spam asterischi - Stampa pulita dei dettagli iniziali
    print(f"\nCASO: {scen['vittima'].upper()}")

    # Genera e stampa il prologo narrativo (evitando spoiler tramite logica dedicata)
    print(engine.genera_intro_narrativa())

    print("\nRAPPORTO FORENSE:")
    for f in scen['rapporto_forense']:
        print(f"- {f}")

    # --- LOOP PRINCIPALE DEL GIOCO ---
    # Ciclo infinito che gestisce i turni fino alla risoluzione o all'uscita
    while True:
        # Rimosso spam uguali (====)
        # Mostra la lista dei sospettati e le piste iniziali per guidare il giocatore
        print("\nSOSPETTATI & PISTE")
        for s in scen['sospettati']:
            print(f"[{s['id']}] {s['nome'].upper()} ({s['ruolo']})")
            print(f"    Pista: {s['indizio_iniziale']}")
            print("")  # Solo uno spazio vuoto invece della linea tratteggiata

        # Opzioni di sistema e di risoluzione
        print("S. Salva ed Esci")
        print("A. ACCUSA E RISOLVI IL CASO")

        inp = input("> ").upper().strip()

        # --- OPZIONE SALVATAGGIO ---
        # Permette di salvare lo stato attuale (inclusi turni ed eventi) su JSON
        if inp == 'S':
            print("\nNome salvataggio (Invio per auto):")
            nome_user = input("> ").strip()
            # Chiama il metodo di salvataggio del motore
            msg = engine.salva_partita(nome_user if nome_user else None)
            print(msg)
            break  # Esce dal gioco dopo il salvataggio

        # --- OPZIONE ACCUSA (RISOLUZIONE) ---
        # Fase finale: il giocatore formula l'ipotesi e il sistema verifica la Ground Truth
        elif inp == 'A':
            # Rimosso spam punti esclamativi
            print("\nFASE FINALE: ACCUSA")
            print("Chi è il colpevole?")

            try:
                id_accusa = int(input("ID sospettato > "))

                # Trova l'oggetto sospettato scelto dall'utente
                sospettato_scelto = next((s for s in scen['sospettati'] if s['id'] == id_accusa), None)
                # Trova l'oggetto del vero colpevole (Ground Truth)
                vero_colpevole = next(s for s in scen['sospettati'] if s['colpevole'])

                if not sospettato_scelto:
                    print("ID non valido.")
                    continue

                print(f"\nArresto di {sospettato_scelto['nome']} in corso...")
                time.sleep(1)

                # Verifica logica: Confronta la scelta utente con la verità nel JSON
                if sospettato_scelto['colpevole']:
                    print("\nCASO RISOLTO.")
                    print(f"L'assassino era {vero_colpevole['nome']}.")
                else:
                    print(f"\nERRORE. {sospettato_scelto['nome']} è INNOCENTE.")
                    print(f"Il vero assassino era {vero_colpevole['nome']}.")

                # Rivela la verità completa (Ground Truth) per confronto
                print("\nVERITÀ (GROUND TRUTH)")
                print(f"Movente: {scen['movente_reale']}")
                print(f"Arma: {scen['arma_reale']}")
                print(f"Alibi Reale del Killer: FALSO ({vero_colpevole['alibi']})")
                print(f"Segreto: {vero_colpevole['segreto']}")

                break  # Fine del gioco

            except ValueError:
                print("Inserire un numero.")

        # --- OPZIONE INTERROGATORIO ---
        # Se l'input è un numero, avvia l'interrogatorio del sospettato corrispondente
        elif inp.isdigit():
            id_s = int(inp)
            # Verifica range ID (assumendo 3 sospettati: 0, 1, 2)
            if 0 <= id_s < 3:
                nome_sosp = scen['sospettati'][id_s]['nome']
                print(f"\nINTERROGATORIO: {nome_sosp}")
                print("(Scrivi 'FINE' per terminare)")

                history = []  # Memoria locale della conversazione corrente

                # Loop interno di chat con il singolo sospettato
                while True:
                    d = input("DETECTIVE: ")

                    # Comando per terminare l'interrogatorio e generare il report
                    if d.upper() == 'FINE':
                        if not history:
                            break

                        # Rimosso spam puntini (...)
                        print("\nGenerazione rapporto analista...")

                        # Chiama l'LLM in modalità "Analista" per verificare la coerenza delle risposte
                        rapporto = engine.genera_rapporto_polizia(id_s, history)

                        print("\nRAPPORTO POLIZIA")
                        print(f"Soggetto: {nome_sosp.upper()}")
                        print(rapporto)
                        input("\n(Premi Invio)")
                        break

                    # Elabora la risposta del sospettato:
                    # 1. Recupero RAG
                    # 2. Generazione LLM
                    # 3. Verifica Neuro-Simbolica (Grafo)
                    r = engine.elabora_turno(id_s, d, history)
                    print(f"SOSPETTATO: {r}")
                    history.append(f"D: {d} R: {r}")

                    # Verifica se scatta un colpo di scena (Evento Dinamico)
                    # Controlla il numero di turni globali e inietta nuovi fatti se necessario
                    evento = engine.verifica_colpo_scena()
                    if evento:
                        print("\n" + "!" * 50)
                        print("BREAKING NEWS - AGGIORNAMENTO CENTRALE")
                        print(f"RAPPORTO URGENTE: {evento}")
                        print("")
                        print("(Nota: I sospettati sono ora al corrente di questo fatto)")

                        # Piccola pausa per enfasi drammatica
                        time.sleep(2)


if __name__ == "__main__":
    main()