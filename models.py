from pydantic import BaseModel, Field
from typing import List

# --- DEFINIZIONE CLASSI PYDANTIC ---
class Sospettato(BaseModel):
    id: int
    nome: str = Field(..., description="Nome e cognome del sospettato")
    ruolo: str = Field(..., description="Il mestiere o ruolo sociale (es. Maggiordomo, Amante)")
    colpevole: bool = Field(..., description="True se è l'assassino, False altrimenti")
    personalita: str = Field(..., description="3 aggettivi che descrivono il carattere")
    alibi: str = Field(..., description="L'alibi fornito (falso se colpevole, vero se innocente)")
    segreto: str = Field(..., description="Un segreto oscuro o un dettaglio sospetto")
    indizio_iniziale: str = Field(..., description="Il motivo specifico per cui è sospettato (es. 'Visto litigare', 'Le sue impronte sono sulla porta', 'Era l'unico con le chiavi')")

class ScenarioInvestigativo(BaseModel):
    vittima: str = Field(..., description="Nome della vittima")
    luogo_omicidio: str = Field(..., description="Ambientazione noir dettagliata")
    arma_reale: str = Field(..., description="L'oggetto usato per l'omicidio")
    movente_reale: str = Field(..., description="Il motivo profondo dell'omicidio")
    intro_atmosfera: str = Field(..., description="Descrizione sensoriale del meteo e luci")
    rapporto_forense: List[str] = Field(..., description="Lista di 3 fatti oggettivi e scientifici trovati sulla scena")
    sospettati: List[Sospettato] = Field(..., description="Lista esattamente di 3 sospettati")