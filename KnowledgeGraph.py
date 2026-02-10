import networkx as nx
import matplotlib.pyplot as plt


class KnowledgeGraph:
    """
    Classe che gestisce la componente Simbolica (Logic Layer) del sistema Neuro-Simbolico.
    Utilizza un grafo (NetworkX) per modellare le relazioni tra entità, prove e sospettati,
    rappresentando la "Ground Truth" (Verità Oggettiva) verificabile.
    """

    def __init__(self):
        # Inizializzazione del grafo vuoto.
        # Usiamo "self.grafo" come struttura dati principale per memorizzare nodi (entità) e archi (relazioni).
        # Questo garantisce coerenza con le chiamate effettuate dal GameEngine.
        self.grafo = nx.Graph()

    def costruisci_da_scenario(self, scenario):
        """
        Popola il grafo iniziale partendo dai dati strutturati (JSON) dello scenario.
        Trasforma le entità testuali generate dall'LLM in nodi semantici interconnessi.
        """
        # Pulisce il grafo da eventuali dati di partite precedenti per evitare conflitti
        self.grafo.clear()

        # 1. Definizione dei nodi cardine: Vittima e Luogo del delitto
        # Questi nodi fungono da 'hub' centrali per le relazioni spaziali e personali
        self.grafo.add_node(scenario['vittima'], tipo="VITTIMA")
        self.grafo.add_node(scenario['luogo_omicidio'], tipo="LUOGO")
        # Crea l'arco che lega la vittima alla scena del crimine
        self.grafo.add_edge(scenario['vittima'], scenario['luogo_omicidio'], relazione="trovata a")

        # 2. Inserimento dei Sospettati e delle loro Relazioni Base
        for s in scenario['sospettati']:
            # Ogni sospettato è un nodo con attributi specifici (ruolo)
            self.grafo.add_node(s['nome'], tipo="SOSPETTATO", ruolo=s['ruolo'])

            # Relazione sociale con la vittima (base di partenza per tutti i sospettati)
            self.grafo.add_edge(s['nome'], scenario['vittima'], relazione="conosceva")

            # Relazione spaziale/logica basata sull'indizio che ha portato al fermo
            # Questo collega il sospettato alla scena del crimine nel grafo
            self.grafo.add_edge(s['nome'], scenario['luogo_omicidio'], relazione="collegato da indizio")

        # 3. Inserimento dei Fatti Forensi (Prove)
        # Ogni elemento del rapporto forense diventa un nodo 'PROVA'
        for fatto in scenario['rapporto_forense']:
            self.grafo.add_node(fatto, tipo="PROVA")
            # Le prove sono collegate logicamente alla vittima
            self.grafo.add_edge(fatto, scenario['vittima'], relazione="riguarda")

    def ottieni_fatti_su(self, entita_nome):
        """
        Funzione di Retrieval Simbolico.
        Dato il nome di un'entità (es. un sospettato), restituisce una lista di stringhe
        che descrivono tutte le relazioni note e verificate nel grafo.

        Usata dal Fact-Checker per confrontare le dichiarazioni dell'LLM con la verità.
        """
        # Verifica preliminare: se il nodo non esiste, non ci sono fatti noti
        if entita_nome not in self.grafo:
            return []

        fatti = []
        # Attraversamento del grafo: trova tutti i nodi adiacenti (vicini) all'entità richiesta
        for vicino in self.grafo.neighbors(entita_nome):
            # Recupera l'etichetta della relazione (es. "conosceva", "trovata a")
            relazione = self.grafo[entita_nome][vicino].get('relazione', 'collegato a')
            # Formatta il fatto come tripla semantica leggibile: Soggetto -> Relazione -> Oggetto
            fatti.append(f"{entita_nome} --[{relazione}]--> {vicino}")

        return fatti

    def aggiungi_fatto(self, fatto_testo):
        """
        Metodo per l'evoluzione dinamica del grafo (Dynamic Graph Update).
        Permette di inserire nuovi nodi a runtime quando si verifica un "Plot Twist" (Colpo di Scena),
        aggiornando la Ground Truth senza dover rigenerare l'intero scenario.
        """
        if fatto_testo:
            # Aggiunge il fatto come un nuovo nodo nel grafo con tipo 'EVENTO_DINAMICO'
            # Questo permette alle future query di verifica di includere questo nuovo evento
            # Lo colleghiamo fittiziamente a "INDAGINE" per non lasciarlo isolato, se vuoi
            self.grafo.add_node(fatto_testo, tipo="EVENTO_DINAMICO")

            # (Opzionale) Stampa di debug per confermare l'aggiornamento della struttura dati
            print(f"[GRAFO] Nuovo nodo aggiunto: {fatto_testo[:20]}...")