from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class TypeRapport(str, Enum):
    """Types de rapports disponibles dans Mainos"""
    ANALYSE_MARCHE = "analyse_marche"
    RAPPORT_RISQUE = "rapport_risque"
    NEWSLETTER = "newsletter"
    COURS = "cours"
    ANALYSE_SWOT = "analyse_swot"
    BUSINESS_PLAN = "business_plan"
    ETUDE_COMPETITIVE = "etude_competitive"

class TonRapport(str, Enum):
    """Tons disponibles pour les rapports"""
    PROFESSIONNEL = "professionnel"
    ACADEMIQUE = "academique"
    INFORMATIF = "informatif"
    CONVERSATIONNEL = "conversationnel"
    PRUDENT = "prudent"
    OPTIMISTE = "optimiste"
    PEDAGOGIQUE = "pedagogique"
    ANALYTIQUE = "analytique"

class LongueurRapport(str, Enum):
    """Longueurs disponibles pour les rapports"""
    COURTE = "courte"
    MOYENNE = "moyenne"
    DETAILLEE = "detaillee"

class FormatOutput(str, Enum):
    """Formats de sortie disponibles"""
    MARKDOWN = "markdown"
    PDF = "pdf"
    PPTX = "pptx"
    HTML = "html"
    DOCX = "docx"

class PlateformeIntegration(str, Enum):
    """Plateformes d'intégration disponibles"""
    NOTION = "notion"
    GOOGLE_DOCS = "google_docs"
    TRELLO = "trello"
    SLACK = "slack"
    MIRO = "miro"

class MainosState(BaseModel):
    """État complet pour une requête Mainos"""
    topic: str
    type_rapport: TypeRapport = TypeRapport.ANALYSE_MARCHE
    ton: TonRapport = TonRapport.PROFESSIONNEL
    longueur: LongueurRapport = LongueurRapport.MOYENNE
    format_sortie: List[FormatOutput] = [FormatOutput.MARKDOWN]
    benchmark_qualite: bool = True
    options_specifiques: Dict[str, Any] = {}
    
class MainosReport(BaseModel):
    """Structure de rapport final de Mainos"""
    report_id: str
    topic: str
    type_rapport: str
    contenu: Dict[str, Any]
    metadata: Dict[str, Any]
    benchmark_score: Optional[float] = None
    formats_disponibles: List[str] = ["markdown"]
    
class MainosRequest(BaseModel):
    """Structure de requête pour l'API Mainos"""
    topic: str
    type_rapport: str = TypeRapport.ANALYSE_MARCHE
    ton: str = TonRapport.PROFESSIONNEL
    longueur: str = LongueurRapport.MOYENNE
    format_sortie: List[str] = [FormatOutput.MARKDOWN]
    benchmark_qualite: bool = True
    options_specifiques: Dict[str, Any] = {}

class MainosResponse(BaseModel):
    """Structure de réponse standard pour l'API Mainos"""
    report_id: str
    status: str
    message: str 