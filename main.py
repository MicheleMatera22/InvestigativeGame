from GameEngine import GameEngine
from config import Config


def main():
    engine = GameEngine()

    print("=== AI DETECTIVE SYSTEM v2.0 ===")
    print("1. Nuova Indagine")
    print("2. Carica Salvataggio")
    scelta = input("> ")

    if scelta == '2':
        if engine.carica_partita():
            print("Partita caricata con successo!")
        else:
            print("Nessun salvataggio trovato. Genero nuovo...")
            scelta = '1'

    if scelta == '1':
        if not engine.genera_nuova_partita():
            print("Errore critico generazione.")
            return

    # Intro
    scen = engine.scenario
    print(f"\nCASO: {scen['vittima']} - {scen['luogo_omicidio']}")
    print("RAPPORTO:")
    for f in scen['rapporto_forense']: print(f"- {f}")

    # Loop Principale
    while True:
        print("\n--- LISTA SOSPETTATI & PISTE ---")

        # --- MODIFICA QUI: Visualizzazione arricchita ---
        for s in scen['sospettati']:
            print(f"[{s['id']}] {s['nome'].upper()} ({s['ruolo']})")
            # Qui stampiamo l'indizio per risolvere il "Cold Start Problem"
            # Nota: Funziona solo se hai aggiornato models.py e GameEngine.py come detto prima
            print(f"    ► MOTIVO DEL FERMO: {s['indizio_iniziale']}")
            print("-" * 40)

        print("S. Salva ed Esci")
        # -----------------------------------------------

        inp = input("> ").upper()
        if inp == 'S':
            engine.salva_partita()
            print("Salvato. Arrivederci.")
            break

        if inp.isdigit():
            id_s = int(inp)
            if 0 <= id_s < 3:
                # Sotto-loop di interrogatorio
                print(f"--- Interrogatorio ID {id_s} (Scrivi 'FINE' per uscire) ---")
                print(f"(Suggerimento: Chiedi riguardo a: {scen['sospettati'][id_s]['indizio_iniziale']})")

                history = []
                while True:
                    d = input("DETECTIVE: ")
                    if d.upper() == 'FINE': break

                    # Chiamata all'Engine
                    r = engine.elabora_turno(id_s, d, history)
                    print(f"SOSPETTATO: {r}")
                    history.append(f"D: {d} R: {r}")


if __name__ == "__main__":
    main()