import networkx as nx
import matplotlib.pyplot as plt


class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def costruisci_da_scenario(self, scenario):
        print("--- Costruzione Knowledge Graph ---")
        vittima = scenario['vittima']
        arma = scenario['arma_reale']

        self.graph.add_edge(vittima, scenario['luogo_omicidio'], relation="TROVATA_A")
        self.graph.add_edge(vittima, arma, relation="UCCISA_CON")

        for s in scenario['sospettati']:
            self.graph.add_edge(s['nome'], s['ruolo'], relation="LAVORA_COME")
            if s['colpevole']:
                self.graph.add_edge(s['nome'], vittima, relation="HA_UCCISO")
                self.graph.add_edge(s['nome'], arma, relation="HA_USATO")
                self.graph.add_edge(s['nome'], "Falso", relation="ALIBI_STATUS")
            else:
                self.graph.add_edge(s['nome'], "Vero", relation="ALIBI_STATUS")

        print(f"Grafo: {self.graph.number_of_nodes()} nodi creati.")

    def ottieni_fatti_su(self, entita):
        fatti = []
        if self.graph.has_node(entita):
            for _, obj, data in self.graph.out_edges(entita, data=True):
                fatti.append(f"{entita} -> {data['relation']} -> {obj}")
        return fatti

    def visualizza(self):
        try:
            pos = nx.spring_layout(self.graph)
            nx.draw(self.graph, pos, with_labels=True, node_color='lightblue')
            labels = nx.get_edge_attributes(self.graph, 'relation')
            nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=labels)
            plt.show()
        except Exception as e:
            print(f"Errore visualizzazione: {e}")