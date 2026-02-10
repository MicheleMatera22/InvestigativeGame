from pydantic import BaseModel, Field
from typing import List


# --- DEFINIZIONE CLASSI PYDANTIC ---
# Questo modulo rappresenta il "Data Layer" (Livello Dati) dell'architettura.
# Utilizza la libreria Pydantic per definire schemi rigidi di validazione.
# Ruolo nella tesi: Garantire che l'output probabilistico dell'LLM (Llama 3.2)
# venga trasformato in strutture dati deterministiche e utilizzabili dal codice.

class Sospettato(BaseModel):
    """
    Modello dati che rappresenta un singolo NPC (Non-Player Character).
    Definisce gli attributi fisici, psicologici e logici necessari per la simulazione.
    """
    id: int
    nome: str = Field(..., description="Nome e cognome del sospettato")
    ruolo: str = Field(..., description="Il mestiere o ruolo sociale (es. Maggiordomo, Amante)")

    # Campo booleano fondamentale per la logica di gioco (Ground Truth).
    # Determina se l'NPC deve mentire o dire la verità sul crimine.
    colpevole: bool = Field(..., description="True se è l'assassino, False altrimenti")

    personalita: str = Field(..., description="3 aggettivi che descrivono il carattere")
    alibi: str = Field(..., description="L'alibi fornito (falso se colpevole, vero se innocente)")
    segreto: str = Field(..., description="Un segreto oscuro o un dettaglio sospetto")

    # Questo campo guida il giocatore nella scelta iniziale ("Cold Start Problem")
    indizio_iniziale: str = Field(...,
                                  description="Il motivo specifico per cui è sospettato (es. 'Visto litigare', 'Le sue impronte sono sulla porta', 'Era l'unico con le chiavi')")


class ScenarioInvestigativo(BaseModel):
    """
    Modello 'Root' (Radice) che incapsula l'intero stato narrativo di una partita.
    Contiene la vittima, il setting e la lista annidata degli oggetti Sospettato.
    """
    vittima: str = Field(..., description="Nome della vittima")
    luogo_omicidio: str = Field(..., description="Ambientazione noir dettagliata")
    arma_reale: str = Field(..., description="L'oggetto usato per l'omicidio")
    movente_reale: str = Field(..., description="Il motivo profondo dell'omicidio")
    intro_atmosfera: str = Field(..., description="Descrizione sensoriale del meteo e luci")

    # Lista di stringhe che verranno usate per costruire i nodi 'PROVA' nel Knowledge Graph
    rapporto_forense: List[str] = Field(..., description="Lista di 3 fatti oggettivi e scientifici trovati sulla scena")

    # Relazione 1-a-Molti: Uno scenario contiene esattamente 3 sospettati strutturati
    sospettati: List[Sospettato] = Field(..., description="Lista esattamente di 3 sospettati")