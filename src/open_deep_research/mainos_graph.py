from typing import Literal, Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig

from langgraph.constants import Send
from langgraph.graph import START, END, StateGraph
from langgraph.types import interrupt, Command

# Importer les modules existants
from .state import ReportStateInput, ReportStateOutput, Sections, ReportState, SectionState, SectionOutputState, Queries, Feedback
from .prompts import report_planner_query_writer_instructions, report_planner_instructions
from .configuration import Configuration
from .utils import tavily_search_async, deduplicate_and_format_sources, format_sections, perplexity_search, get_config_value

# Importer les nouveaux modules Mainos
from .mainos_types import MainosState, TypeRapport
from .mainos_prompts import get_report_instructions, SECTION_WRITER_INSTRUCTIONS

# Importer le graphe existant
from .graph import graph as base_graph, generate_report_plan, generate_queries_and_search, create_report_plan, write_section

async def adapt_mainos_to_report_state(mainos_state: MainosState) -> ReportState:
    """
    Adapte l'état Mainos à l'état ReportState utilisé par le graphe de base
    
    Args:
        mainos_state: État Mainos à adapter
        
    Returns:
        État ReportState compatible avec le graphe de base
    """
    # Créer un ReportState à partir des données Mainos
    report_state = {
        "topic": mainos_state["topic"],
        "queries": [],
        "search_results": [],
        "report_plan": {},
        "sections": {},
    }
    
    # Ajouter des métadonnées pour le traitement spécifique à Mainos
    report_state["mainos_metadata"] = {
        "type_rapport": mainos_state.get("type_rapport", TypeRapport.ANALYSE_MARCHE),
        "ton": mainos_state.get("ton", "professionnel"),
        "longueur": mainos_state.get("longueur", "moyenne"),
        "benchmark_qualite": mainos_state.get("benchmark_qualite", True),
        "options_specifiques": mainos_state.get("options_specifiques", {})
    }
    
    return report_state

async def adapt_report_state_to_mainos(report_state: ReportState) -> Dict[str, Any]:
    """
    Adapte l'état ReportState de retour vers un format compatible avec Mainos
    
    Args:
        report_state: État ReportState à adapter
        
    Returns:
        État au format attendu par Mainos
    """
    # Extraire les données pertinentes
    sections = report_state.get("sections", {})
    formatted_sections = {}
    
    # Formater les sections
    for section_title, section_data in sections.items():
        if isinstance(section_data, dict) and "output" in section_data:
            formatted_sections[section_title] = section_data["output"]
        else:
            formatted_sections[section_title] = section_data
    
    # Construire le résultat
    result = {
        "title": report_state.get("title", report_state.get("topic", "Rapport")),
        "sections": formatted_sections,
        "sources": report_state.get("sources", [])
    }
    
    return result

async def modify_report_plan_for_type(state: ReportState, config: RunnableConfig):
    """
    Fonction pour adapter le plan de rapport au type spécifique de rapport Mainos
    
    Args:
        state: L'état actuel
        config: La configuration
        
    Returns:
        L'état modifié
    """
    # Récupérer les métadonnées Mainos
    mainos_metadata = state.get("mainos_metadata", {})
    topic = state["topic"]
    type_rapport = mainos_metadata.get("type_rapport", TypeRapport.ANALYSE_MARCHE)
    ton = mainos_metadata.get("ton", "professionnel")
    longueur = mainos_metadata.get("longueur", "moyenne")
    
    # Obtenir les instructions spécifiques au type de rapport
    instructions = get_report_instructions(type_rapport, topic, ton, longueur)
    
    # Configurer le modèle
    configurable = Configuration.from_runnable_config(config)
    planner_provider = get_config_value(configurable.planner_provider)
    planner_model_name = get_config_value(configurable.planner_model)
    planner_model = init_chat_model(model=planner_model_name, model_provider=planner_provider, temperature=0)
    
    # Préparer les messages
    messages = [
        SystemMessage(content=instructions),
        HumanMessage(content=f"Générez un plan structuré pour un rapport de type '{type_rapport}' sur le sujet: {topic}")
    ]
    
    # Appeler le modèle
    response = await planner_model.ainvoke(messages)
    plan_text = response.content
    
    # Parser le plan pour extraire les sections
    sections = {}
    current_section = None
    
    for line in plan_text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Détecter les titres de section (numérotés ou avec des titres clairs)
        if line[0].isdigit() and '.' in line[:5]:
            # Format "1. Titre de section"
            section_title = line[line.find('.')+1:].strip()
            current_section = section_title
            sections[current_section] = {"title": current_section, "content": ""}
        elif line.lower().startswith(('introduction', 'conclusion', 'résumé', 'résumé exécutif', 'méthodologie', 'contexte')):
            # Sections communes sans numérotation
            current_section = line
            sections[current_section] = {"title": current_section, "content": ""}
    
    # Si aucune section n'a été détectée, utiliser le texte entier
    if not sections:
        sections = {
            "Introduction": {"title": "Introduction", "content": ""},
            "Développement": {"title": "Développement", "content": ""},
            "Conclusion": {"title": "Conclusion", "content": ""}
        }
    
    # Mettre à jour l'état
    state["report_plan"] = sections
    
    return state

async def mainos_invoke(input_state: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Point d'entrée principal pour invoquer le graphe avec les paramètres Mainos
    
    Args:
        input_state: État d'entrée au format Mainos
        config: Configuration optionnelle
        
    Returns:
        Résultat du traitement
    """
    # Adapter l'état d'entrée au format attendu par le graphe de base
    report_state = await adapt_mainos_to_report_state(input_state)
    
    # Ajouter le nœud de modification du plan à la configuration
    runnable_config = config or {}
    
    # Invoquer le graphe de base
    result = await base_graph.ainvoke(report_state, runnable_config)
    
    # Adapter le résultat au format attendu par Mainos
    mainos_result = await adapt_report_state_to_mainos(result)
    
    return mainos_result

# Créer un nouveau graphe adapté à Mainos
def create_mainos_graph():
    """Crée un nouveau graphe adapté aux besoins de Mainos"""
    # Créer un nouveau graphe
    workflow = StateGraph(ReportState)
    
    # Ajouter les nœuds
    workflow.add_node("adapt_input", adapt_mainos_to_report_state)
    workflow.add_node("generate_queries_and_search", generate_queries_and_search)
    workflow.add_node("modify_report_plan_for_type", modify_report_plan_for_type)
    workflow.add_node("create_report_plan", create_report_plan)
    workflow.add_node("write_section", write_section)
    workflow.add_node("adapt_output", adapt_report_state_to_mainos)
    
    # Définir les transitions
    workflow.add_edge(START, "adapt_input")
    workflow.add_edge("adapt_input", "generate_queries_and_search")
    workflow.add_edge("generate_queries_and_search", "modify_report_plan_for_type")
    workflow.add_edge("modify_report_plan_for_type", "create_report_plan")
    workflow.add_edge("create_report_plan", "write_section")
    
    # Condition pour continuer à écrire des sections ou terminer
    def are_all_sections_written(state: ReportState):
        sections = state.get("sections", {})
        report_plan = state.get("report_plan", {})
        
        # Vérifier si toutes les sections du plan ont été écrites
        for section_title in report_plan:
            if section_title not in sections:
                return False
        
        return True
    
    # Ajouter les conditions
    workflow.add_conditional_edges(
        "write_section",
        are_all_sections_written,
        {
            True: "adapt_output",
            False: "write_section"
        }
    )
    
    workflow.add_edge("adapt_output", END)
    
    # Compiler le graphe
    return workflow.compile()

# Créer le graphe Mainos
mainos_graph = create_mainos_graph()

# Exposer une fonction d'invocation simplifiée
async def generate_report(topic: str, type_rapport: str = "analyse_marche", ton: str = "professionnel", 
                     longueur: str = "moyenne", benchmark_qualite: bool = True,
                     options_specifiques: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Génère un rapport selon les paramètres spécifiés
    
    Args:
        topic: Le sujet du rapport
        type_rapport: Le type de rapport à générer
        ton: Le ton à utiliser
        longueur: La longueur souhaitée
        benchmark_qualite: Activer ou non l'évaluation de qualité
        options_specifiques: Options spécifiques au type de rapport
        
    Returns:
        Le rapport généré
    """
    # Créer l'état d'entrée
    input_state = {
        "topic": topic,
        "type_rapport": type_rapport,
        "ton": ton,
        "longueur": longueur,
        "benchmark_qualite": benchmark_qualite,
        "options_specifiques": options_specifiques or {}
    }
    
    # Invoquer le graphe
    return await mainos_graph.ainvoke(input_state) 