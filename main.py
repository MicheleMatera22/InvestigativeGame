import time
from GameEngine import GameEngine


def main():
    """
    Funzione principale (Entry Point) dell'applicazione.
    Gestisce il ciclo di vita del gioco: inizializzazione, menu,
    loop di gioco principale e interazione utente.
    """

    # Inizializzazione del motore di gioco
    engine = GameEngine()

    # --- MENU PRINCIPALE ---
    print("\n" + "═" * 40)
    print("      NEURO-SYMBOLIC DETECTIVE      ")
    print("═" * 40)
    print("1. Nuova Indagine")
    print("2. Carica Salvataggio")
    print("-" * 40)

    scelta = input("> ")

    # --- GESTIONE MENU INIZIALE ---
    if scelta == '2':
        saves = engine.elenca_salvataggi()

        if not saves:
            print("\n[!] Nessun salvataggio trovato.")
            print("Avvio nuova indagine...")
            scelta = '1'
        else:
            print("\n[ ARCHIVIO CASI ]")
            for i, file in enumerate(saves):
                print(f"  {i + 1}. {file}")
            print("  0. Indietro")

            try:
                idx = int(input("\nScegli file > "))
                if 1 <= idx <= len(saves):
                    filename_scelto = saves[idx - 1]
                    print(f"\nRecupero fascicolo '{filename_scelto}'...")

                    if engine.carica_partita(filename_scelto):
                        print("Dati caricati con successo.")
                    else:
                        print("Errore nel caricamento.")
                        return
                else:
                    scelta = '1'
            except ValueError:
                scelta = '1'

    # --- GENERAZIONE NUOVA PARTITA ---
    if scelta == '1':
        if not engine.genera_nuova_partita():
            print("Errore critico generazione.")
            return

    # --- INTRODUZIONE AL CASO ---
    scen = engine.scenario

    print("\n" + "-" * 50)
    print(f" CASO APERTO: {scen['vittima'].upper()}")
    print("-" * 50)

    print(engine.genera_intro_narrativa())

    print("\n[ RAPPORTO FORENSE ]")
    for f in scen['rapporto_forense']:
        print(f" • {f}")

    # --- LOOP PRINCIPALE DEL GIOCO ---
    while True:
        # Mostra la lista dei sospettati in modo pulito
        print("\n" + "-" * 30)
        print(" SQUADRA SOSPETTATI & PISTE")
        print("-" * 30)

        for s in scen['sospettati']:
            print(f" [{s['id']}] {s['nome'].upper()} | {s['ruolo']}")
            print(f"      Pista: {s['indizio_iniziale']}")

        print("-" * 30)
        print("[OPZIONI]")
        print("  S. Salva ed Esci")
        print("  A. ACCUSA E RISOLVI IL CASO")

        inp = input("\n> ").upper().strip()

        # --- OPZIONE SALVATAGGIO ---
        if inp == 'S':
            print("\nNome salvataggio (Invio per nome auto):")
            nome_user = input("> ").strip()
            msg = engine.salva_partita(nome_user if nome_user else None)
            print(f"\n>> {msg}")
            break

        # --- OPZIONE ACCUSA ---
        elif inp == 'A':
            print("\n" + "═" * 40)
            print("      FASE FINALE: L'ACCUSA      ")
            print("═" * 40)
            print("Chi è il colpevole?")

            try:
                id_accusa = int(input("ID sospettato > "))

                sospettato_scelto = next((s for s in scen['sospettati'] if s['id'] == id_accusa), None)
                vero_colpevole = next(s for s in scen['sospettati'] if s['colpevole'])

                if not sospettato_scelto:
                    print("[!] ID non valido.")
                    continue

                print(f"\nEsecuzione mandato di arresto per {sospettato_scelto['nome']}...")
                time.sleep(1)

                if sospettato_scelto['colpevole']:
                    print("\n[ ESITO: SUCCESSO ]")
                    print(f"CASO RISOLTO. L'assassino era {vero_colpevole['nome']}.")
                else:
                    print(f"\n[ ESITO: FALLIMENTO ]")
                    print(f"ERRORE GIUDIZIARIO. {sospettato_scelto['nome']} è INNOCENTE.")
                    print(f"Il vero assassino era {vero_colpevole['nome']}.")

                # Ground Truth formattata
                print("\n" + "-" * 40)
                print(" VERITÀ OGGETTIVA (GROUND TRUTH)")
                print("-" * 40)
                print(f" • Movente: {scen['movente_reale']}")
                print(f" • Arma:    {scen['arma_reale']}")
                print(f" • Alibi del Killer: FALSO ({vero_colpevole['alibi']})")
                print(f" • Segreto: {vero_colpevole['segreto']}")
                print("-" * 40)

                break

            except ValueError:
                print("Inserire un numero valido.")

        # --- OPZIONE INTERROGATORIO ---
        elif inp.isdigit():
            id_s = int(inp)
            if 0 <= id_s < 3:
                nome_sosp = scen['sospettati'][id_s]['nome']
                print(f"\n--- SALA INTERROGATORI: {nome_sosp.upper()} ---")
                print("(Digita 'FINE' per terminare)")

                history = []
                while True:
                    d = input("\n[DETECTIVE]: ")

                    if d.upper() == 'FINE':
                        if not history:
                            break

                        print("\nElaborazione rapporto analista in corso...")

                        rapporto = engine.genera_rapporto_polizia(id_s, history)

                        print("\n[ RAPPORTO ANALITICO ]")
                        print(f"Soggetto: {nome_sosp.upper()}")
                        print(f"Esito: {rapporto}")
                        input("\n(Premi Invio per continuare)")
                        break

                    # Elaborazione turno
                    r = engine.elabora_turno(id_s, d, history)
                    print(f"[SOSPETTATO]: {r}")
                    history.append(f"Detective: {d} | Sospettato: {r}")

                    # --- GESTIONE EVENTI (PLOT TWIST) ---
                    evento = engine.verifica_colpo_scena()
                    if evento:
                        print(" [!] AGGIORNAMENTO DALLA CENTRALE")
                        print("-" * 60)
                        print(f" RAPPORTO URGENTE: {evento}")
                        print("-" * 60)

                        time.sleep(2)

    engine.apri_questionario()

if __name__ == "__main__":
    main()