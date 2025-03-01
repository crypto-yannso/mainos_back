from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Query, Path, File, UploadFile
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import tempfile
import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import io

from pydantic import BaseModel

from .mainos_types import (
    MainosRequest, 
    MainosResponse, 
    MainosReport, 
    TypeRapport, 
    FormatOutput,
    PlateformeIntegration
)
from .benchmark import QualityBenchmark
from .export import exporter_rapport, integrer_avec_plateforme
from .auth import verify_api_key  # Importer la fonction d'authentification

# Importer le graphe existant
from .graph import graph

# Base de données en mémoire pour les rapports et les tâches
class MemoryStore:
    """Stockage en mémoire pour les rapports et les tâches"""
    
    def __init__(self):
        self.tasks = {}  # Statut des tâches
        self.reports = {}  # Rapports générés
        self.exports = {}  # Formats exportés

memory_store = MemoryStore()

# Création de l'application FastAPI
app = FastAPI(
    title="Mainos API",
    description="API pour la plateforme Mainos de génération de rapports intelligents",
    version="1.0.0"
)

# Configuration CORS pour permettre les requêtes cross-origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, remplacez par les domaines spécifiques
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles pour les requêtes et réponses spécifiques à l'API
class ExportRequest(BaseModel):
    """Requête pour exporter un rapport dans un format spécifique"""
    format: str
    options: Optional[Dict[str, Any]] = None

class IntegrationRequest(BaseModel):
    """Requête pour intégrer un rapport à une plateforme externe"""
    plateforme: str
    credentials: Dict[str, str]
    options: Optional[Dict[str, Any]] = None

class BenchmarkResponse(BaseModel):
    """Réponse pour les métriques de benchmark"""
    report_id: str
    score: float
    criteria_scores: Dict[str, float]
    recommendations: List[str]


# Routes API
@app.get("/")
async def root():
    """Page d'accueil de l'API Mainos"""
    return {
        "message": "Bienvenue sur l'API Mainos",
        "documentation": "/docs",
        "version": "1.0.0"
    }

@app.post("/api/rapport", response_model=MainosResponse)
async def creer_rapport(
    request: MainosRequest, 
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)  # Ajouter la dépendance d'authentification
):
    """
    Crée un nouveau rapport basé sur les paramètres spécifiés
    
    - **topic**: Le sujet du rapport
    - **type_rapport**: Le type de rapport à générer (analyse_marche, rapport_risque, etc.)
    - **ton**: Le ton à utiliser (professionnel, informatif, etc.)
    - **longueur**: La longueur souhaitée (courte, moyenne, detaillee)
    - **format_sortie**: Les formats de sortie souhaités (markdown, pdf, etc.)
    - **benchmark_qualite**: Activer ou non l'évaluation de qualité
    - **options_specifiques**: Options spécifiques au type de rapport
    """
    # Générer un identifiant unique pour le rapport
    report_id = str(uuid.uuid4())
    
    # Enregistrer la tâche comme "en cours"
    memory_store.tasks[report_id] = "running"
    
    # Fonction pour exécuter le graphe en arrière-plan
    async def run_report_generation():
        try:
            # Configuration pour le graphe
            planner_provider = request.options_specifiques.get("planner_provider", "openai") if request.options_specifiques else "openai"
            planner_model = request.options_specifiques.get("planner_model", "gpt-4o") if request.options_specifiques else "gpt-4o"
            writer_provider = request.options_specifiques.get("writer_provider", "anthropic") if request.options_specifiques else "anthropic"
            writer_model = request.options_specifiques.get("writer_model", "claude-3-sonnet-20240229") if request.options_specifiques else "claude-3-sonnet-20240229"
            search_api = request.options_specifiques.get("search_api", "tavily") if request.options_specifiques else "tavily"
            
            # Si OpenAI est spécifié mais une erreur de quota est probable, basculer vers Gemini
            if planner_provider == "openai":
                try:
                    # Vérifier si la clé OpenAI est valide
                    import openai
                    openai.api_key = os.getenv("OPENAI_API_KEY")
                    completion = openai.Completion.create(
                        model="gpt-3.5-turbo-instruct",
                        prompt="Test",
                        max_tokens=5
                    )
                except Exception as e:
                    if "quota" in str(e).lower() or "limit" in str(e).lower() or "rate" in str(e).lower():
                        print(f"OpenAI API indisponible, utilisation de Google Gemini comme alternative: {str(e)}")
                        planner_provider = "google_genai"
                        planner_model = "gemini-1.5-pro"
                        writer_provider = "google_genai"
                        writer_model = "gemini-1.5-pro"
            
            config = {
                "configurable": {
                    "thread_id": report_id,
                    "search_api": search_api,
                    "planner_provider": planner_provider,
                    "planner_model": planner_model,
                    "writer_provider": writer_provider,
                    "writer_model": writer_model,
                    "max_search_depth": 2,
                    "type_rapport": request.type_rapport,
                    "ton": request.ton,
                    "longueur": request.longueur,
                    "format_sortie": request.format_sortie,
                    "benchmark_qualite": request.benchmark_qualite,
                    "options_specifiques": request.options_specifiques
                }
            }
            
            print(f"Génération avec configuration: {config}")
            
            # Appeler le graphe pour générer le rapport
            try:
                result = await graph.ainvoke({"topic": request.topic}, config)
            except Exception as e:
                error_message = str(e)
                print(f"Erreur lors de la génération du rapport: {error_message}")
                
                # Si erreur OpenAI quota, basculer vers Gemini
                if "openai" in error_message.lower() and ("quota" in error_message.lower() or "rate" in error_message.lower()):
                    print("Basculement vers Google Gemini suite à une erreur OpenAI...")
                    config["configurable"]["planner_provider"] = "google_genai"
                    config["configurable"]["planner_model"] = "gemini-1.5-pro"
                    config["configurable"]["writer_provider"] = "google_genai"
                    config["configurable"]["writer_model"] = "gemini-1.5-pro"
                    
                    # Nouvelle tentative avec Gemini
                    result = await graph.ainvoke({"topic": request.topic}, config)
                else:
                    # Autre erreur, relancer
                    raise
            
            # Traiter le résultat
            report_content = {
                "title": result.get("title", f"Rapport sur {request.topic}"),
                "sections": result.get("sections", {}),
                "sources": result.get("sources", []),
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "topic": request.topic,
                    "type_rapport": request.type_rapport,
                    "ton": request.ton,
                    "longueur": request.longueur
                }
            }
            
            # Évaluer la qualité si demandé
            benchmark_score = None
            if request.benchmark_qualite:
                try:
                    benchmark = QualityBenchmark(request.type_rapport)
                    evaluation = await benchmark.evaluate(report_content)
                    benchmark_score = evaluation.get("score", {}).get("overall", 0)
                except Exception as e:
                    print(f"Erreur lors de l'évaluation: {str(e)}")
                    benchmark_score = 0
            
            # Créer le rapport complet
            report = MainosReport(
                report_id=report_id,
                topic=request.topic,
                type_rapport=request.type_rapport,
                contenu=report_content,
                metadata={
                    "ton": request.ton,
                    "longueur": request.longueur,
                    "generated_at": datetime.now().isoformat()
                },
                benchmark_score=benchmark_score,
                formats_disponibles=["markdown"]
            )
            
            # Enregistrer le rapport
            memory_store.reports[report_id] = report
            memory_store.tasks[report_id] = "completed"
            
            # Générer les formats demandés
            for format_output in request.format_sortie:
                if format_output.lower() != "markdown":
                    try:
                        # Convertir le contenu en markdown
                        markdown_content = _convert_report_to_markdown(report.contenu)
                        
                        # Exporter vers le format demandé
                        export_bytes = await asyncio.to_thread(
                            exporter_rapport,
                            contenu=markdown_content, 
                            format_sortie=FormatOutput(format_output.lower()),
                            chemin_sortie=None
                        )
                        
                        # Enregistrer l'export
                        if report_id not in memory_store.exports:
                            memory_store.exports[report_id] = {}
                        
                        memory_store.exports[report_id][format_output.lower()] = export_bytes
                    except Exception as e:
                        print(f"Erreur lors de l'export en {format_output}: {str(e)}")
            
        except Exception as e:
            memory_store.tasks[report_id] = "failed"
            memory_store.reports[report_id] = {"error": str(e)}
            print(f"Erreur lors de la génération du rapport: {str(e)}")
    
    # Démarrer la génération en arrière-plan
    background_tasks.add_task(run_report_generation)
    
    # Retourner la réponse immédiate
    return MainosResponse(
        report_id=report_id,
        status="running",
        message="Génération du rapport lancée"
    )

@app.get("/api/rapport/{report_id}", response_model=Dict[str, Any])
async def obtenir_rapport(report_id: str = Path(..., description="ID du rapport")):
    """
    Obtient le statut ou le contenu d'un rapport
    
    - **report_id**: L'identifiant unique du rapport
    """
    # Vérifier si le rapport existe
    if report_id not in memory_store.tasks:
        raise HTTPException(status_code=404, detail="Rapport non trouvé")
    
    status = memory_store.tasks[report_id]
    
    if status == "running":
        return {
            "status": status,
            "message": "Génération du rapport en cours"
        }
    elif status == "failed":
        return {
            "status": status,
            "error": memory_store.reports[report_id].get("error", "Une erreur inconnue s'est produite")
        }
    elif status == "completed":
        report = memory_store.reports[report_id]
        
        # Mettre à jour les formats disponibles
        formats_disponibles = ["markdown"]
        if report_id in memory_store.exports:
            formats_disponibles.extend(memory_store.exports[report_id].keys())
        
        # Mettre à jour la liste des formats disponibles dans le rapport
        report.formats_disponibles = list(set(formats_disponibles))
        
        return {
            "status": status,
            "report": report.dict(),
            "formats_disponibles": formats_disponibles
        }
    else:
        return {
            "status": "unknown",
            "message": "Statut inconnu"
        }

@app.get("/api/rapport/{report_id}/download")
async def telecharger_rapport(
    report_id: str = Path(..., description="ID du rapport"),
    format: str = Query("markdown", description="Format de téléchargement")
):
    """
    Télécharge un rapport dans le format spécifié
    
    - **report_id**: L'identifiant unique du rapport
    - **format**: Le format de téléchargement (markdown, pdf, pptx, docx, html)
    """
    # Vérifier si le rapport existe
    if report_id not in memory_store.reports:
        raise HTTPException(status_code=404, detail="Rapport non trouvé")
    
    format = format.lower()
    
    # Vérifier si le rapport est complet
    if memory_store.tasks[report_id] != "completed":
        raise HTTPException(status_code=400, detail="Le rapport n'est pas encore prêt")
    
    # Récupérer le rapport
    report = memory_store.reports[report_id]
    
    # Si le format demandé est markdown, le générer à la volée
    if format == "markdown":
        markdown_content = _convert_report_to_markdown(report.contenu)
        
        # Créer une réponse avec le contenu markdown
        return Response(
            content=markdown_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=rapport_{report_id}.md"
            }
        )
    
    # Pour les autres formats, vérifier s'ils sont déjà générés
    if report_id in memory_store.exports and format in memory_store.exports[report_id]:
        # Le format existe déjà, le retourner
        content = memory_store.exports[report_id][format]
        
        # Déterminer le type MIME
        mime_types = {
            "pdf": "application/pdf",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "html": "text/html"
        }
        
        mime_type = mime_types.get(format, "application/octet-stream")
        
        # Créer un flux à partir des bytes
        content_stream = io.BytesIO(content)
        
        # Retourner le contenu comme fichier à télécharger
        return StreamingResponse(
            content_stream,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename=rapport_{report_id}.{format}"
            }
        )
    
    # Le format n'est pas encore généré, le générer à la volée
    try:
        # Convertir en markdown d'abord
        markdown_content = _convert_report_to_markdown(report.contenu)
        
        # Exporter vers le format demandé
        export_bytes = await asyncio.to_thread(
            exporter_rapport,
            contenu=markdown_content, 
            format_sortie=FormatOutput(format),
            chemin_sortie=None
        )
        
        # Sauvegarder pour une utilisation future
        if report_id not in memory_store.exports:
            memory_store.exports[report_id] = {}
        
        memory_store.exports[report_id][format] = export_bytes
        
        # Déterminer le type MIME
        mime_types = {
            "pdf": "application/pdf",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "html": "text/html"
        }
        
        mime_type = mime_types.get(format, "application/octet-stream")
        
        # Créer un flux à partir des bytes
        content_stream = io.BytesIO(export_bytes)
        
        # Retourner le contenu comme fichier à télécharger
        return StreamingResponse(
            content_stream,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename=rapport_{report_id}.{format}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du format {format}: {str(e)}")

@app.post("/api/rapport/{report_id}/integration")
async def integrer_rapport(
    integration_request: IntegrationRequest,
    report_id: str = Path(..., description="ID du rapport")
):
    """
    Intègre un rapport à une plateforme externe
    
    - **report_id**: L'identifiant unique du rapport
    - **plateforme**: La plateforme d'intégration (notion, google_docs, slack, etc.)
    - **credentials**: Les identifiants nécessaires pour l'accès à la plateforme
    - **options**: Options spécifiques à l'intégration
    """
    # Vérifier si le rapport existe
    if report_id not in memory_store.reports:
        raise HTTPException(status_code=404, detail="Rapport non trouvé")
    
    # Vérifier si le rapport est complet
    if memory_store.tasks[report_id] != "completed":
        raise HTTPException(status_code=400, detail="Le rapport n'est pas encore prêt")
    
    # Récupérer le rapport
    report = memory_store.reports[report_id]
    
    # Convertir en markdown
    markdown_content = _convert_report_to_markdown(report.contenu)
    
    try:
        # Exporter vers la plateforme demandée
        result = await asyncio.to_thread(
            integrer_avec_plateforme,
            contenu=markdown_content,
            plateforme=PlateformeIntegration(integration_request.plateforme),
            format_sortie=FormatOutput.MARKDOWN,
            credentials=integration_request.credentials
        )
        
        return {
            "success": True,
            "integration": integration_request.plateforme,
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'intégration avec {integration_request.plateforme}: {str(e)}"
        )

@app.get("/api/rapport/{report_id}/benchmark", response_model=BenchmarkResponse)
async def obtenir_benchmark(report_id: str = Path(..., description="ID du rapport")):
    """
    Obtient les métriques de benchmark pour un rapport
    
    - **report_id**: L'identifiant unique du rapport
    """
    # Vérifier si le rapport existe
    if report_id not in memory_store.reports:
        raise HTTPException(status_code=404, detail="Rapport non trouvé")
    
    # Vérifier si le rapport est complet
    if memory_store.tasks[report_id] != "completed":
        raise HTTPException(status_code=400, detail="Le rapport n'est pas encore prêt")
    
    # Récupérer le rapport
    report = memory_store.reports[report_id]
    
    # Vérifier si l'évaluation a déjà été faite
    if report.benchmark_score is None:
        # Effectuer l'évaluation
        try:
            benchmark = QualityBenchmark(report.type_rapport)
            evaluation = await benchmark.evaluate(report.contenu)
            
            # Mettre à jour le rapport avec le score
            report.benchmark_score = evaluation.get("score", {}).get("overall", 0)
            
            return BenchmarkResponse(
                report_id=report_id,
                score=evaluation.get("score", {}).get("overall", 0),
                criteria_scores=evaluation.get("score", {}).get("criteria", {}),
                recommendations=evaluation.get("recommendations", [])
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'évaluation du rapport: {str(e)}"
            )
    else:
        # Réévaluer le rapport pour obtenir les détails
        try:
            benchmark = QualityBenchmark(report.type_rapport)
            evaluation = await benchmark.evaluate(report.contenu)
            
            return BenchmarkResponse(
                report_id=report_id,
                score=report.benchmark_score,
                criteria_scores=evaluation.get("score", {}).get("criteria", {}),
                recommendations=evaluation.get("recommendations", [])
            )
        except Exception as e:
            # En cas d'erreur, retourner au moins le score global
            return BenchmarkResponse(
                report_id=report_id,
                score=report.benchmark_score,
                criteria_scores={},
                recommendations=["Impossible d'obtenir les détails de l'évaluation"]
            )

@app.patch("/api/rapport/{report_id}")
async def modifier_preferences_rapport(
    report_id: str,
    preferences: Dict[str, Any]
):
    """
    Modifie les préférences d'un rapport en cours ou terminé
    
    - **report_id**: L'identifiant unique du rapport
    - **preferences**: Les nouvelles préférences (format_sortie, ton, etc.)
    """
    # Vérifier si le rapport existe
    if report_id not in memory_store.tasks:
        raise HTTPException(status_code=404, detail="Rapport non trouvé")
    
    # Récupérer le statut
    status = memory_store.tasks[report_id]
    
    if status == "running":
        # Pour un rapport en cours, certaines préférences peuvent être modifiées
        # mais ne prendront effet que pour les étapes restantes
        return {
            "status": "updated",
            "message": "Préférences mises à jour pour les étapes restantes"
        }
    elif status == "completed":
        # Pour un rapport terminé, seules certaines préférences peuvent être modifiées
        # (comme les formats de sortie)
        report = memory_store.reports[report_id]
        
        # Mettre à jour les formats de sortie si spécifiés
        if "format_sortie" in preferences:
            # Générer les nouveaux formats demandés
            for format_output in preferences["format_sortie"]:
                if format_output.lower() != "markdown" and (
                    report_id not in memory_store.exports or 
                    format_output.lower() not in memory_store.exports[report_id]
                ):
                    try:
                        # Convertir le contenu en markdown
                        markdown_content = _convert_report_to_markdown(report.contenu)
                        
                        # Exporter vers le format demandé
                        export_bytes = await asyncio.to_thread(
                            exporter_rapport,
                            contenu=markdown_content, 
                            format_sortie=FormatOutput(format_output.lower()),
                            chemin_sortie=None
                        )
                        
                        # Enregistrer l'export
                        if report_id not in memory_store.exports:
                            memory_store.exports[report_id] = {}
                        
                        memory_store.exports[report_id][format_output.lower()] = export_bytes
                    except Exception as e:
                        print(f"Erreur lors de l'export en {format_output}: {str(e)}")
            
            # Mettre à jour la liste des formats disponibles
            formats_disponibles = ["markdown"]
            if report_id in memory_store.exports:
                formats_disponibles.extend(memory_store.exports[report_id].keys())
            
            report.formats_disponibles = list(set(formats_disponibles))
        
        return {
            "status": "updated",
            "message": "Préférences mises à jour",
            "formats_disponibles": report.formats_disponibles
        }
    else:
        raise HTTPException(
            status_code=400,
            detail="Impossible de modifier les préférences d'un rapport en échec"
        )

@app.get("/api/types")
async def obtenir_types_disponibles():
    """Obtient la liste des types de rapports et formats disponibles"""
    return {
        "types_rapport": [t.value for t in TypeRapport],
        "tons": ["professionnel", "academique", "informatif", "conversationnel", "prudent", "optimiste", "pedagogique", "analytique"],
        "longueurs": ["courte", "moyenne", "detaillee"],
        "formats_sortie": [f.value for f in FormatOutput],
        "plateformes_integration": [p.value for p in PlateformeIntegration]
    }

@app.get("/api/templates/{type_rapport}")
async def obtenir_template_type(type_rapport: str):
    """Obtient un template pour un type de rapport spécifique"""
    try:
        type_enum = TypeRapport(type_rapport)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Type de rapport {type_rapport} non reconnu")
    
    # Templates par défaut selon le type
    templates = {
        TypeRapport.ANALYSE_MARCHE: {
            "title": "Analyse de marché : [SUJET]",
            "structure": [
                "Résumé exécutif",
                "Tendances principales",
                "Analyse des concurrents",
                "Segmentation du marché",
                "Opportunités et défis",
                "Prévisions",
                "Recommandations"
            ],
            "options_specifiques": {
                "inclure_graphiques": True,
                "focus_geographique": "mondial"
            }
        },
        TypeRapport.ANALYSE_SWOT: {
            "title": "Analyse SWOT : [SUJET]",
            "structure": [
                "Résumé",
                "Forces",
                "Faiblesses",
                "Opportunités",
                "Menaces",
                "Recommandations stratégiques"
            ],
            "options_specifiques": {
                "inclure_matrice": True
            }
        },
        # Autres templates par défaut
    }
    
    # Retourner le template demandé ou un template générique
    return templates.get(type_enum, {
        "title": f"{type_rapport.capitalize()} : [SUJET]",
        "structure": [
            "Introduction",
            "Développement",
            "Conclusion"
        ],
        "options_specifiques": {}
    })

# Fonction utilitaire pour convertir un rapport en markdown
def _convert_report_to_markdown(report_content: Dict[str, Any]) -> str:
    """Convertit le contenu d'un rapport en format Markdown"""
    markdown_lines = []
    
    # Titre
    title = report_content.get("title", "Rapport")
    markdown_lines.append(f"# {title}")
    markdown_lines.append("")
    
    # Sections
    sections = report_content.get("sections", {})
    for section_title, section_content in sections.items():
        markdown_lines.append(f"## {section_title}")
        markdown_lines.append("")
        
        if isinstance(section_content, str):
            markdown_lines.append(section_content)
        elif isinstance(section_content, dict) and "content" in section_content:
            markdown_lines.append(section_content["content"])
        elif isinstance(section_content, list):
            markdown_lines.extend(section_content)
        
        markdown_lines.append("")
    
    # Sources
    sources = report_content.get("sources", [])
    if sources:
        markdown_lines.append("## Sources")
        markdown_lines.append("")
        
        for i, source in enumerate(sources, 1):
            if isinstance(source, str):
                markdown_lines.append(f"{i}. {source}")
            elif isinstance(source, dict):
                title = source.get("title", "Source")
                url = source.get("url", "")
                if url:
                    markdown_lines.append(f"{i}. [{title}]({url})")
                else:
                    markdown_lines.append(f"{i}. {title}")
        
        markdown_lines.append("")
    
    return "\n".join(markdown_lines)

@app.post("/api/test-gemini", response_model=Dict[str, Any])
async def tester_gemini(request: Dict[str, Any], api_key: str = Depends(verify_api_key)):
    """Route de test pour Google Gemini sans utiliser LangGraph."""
    try:
        # Récupérer les paramètres de la requête
        prompt = request.get("prompt", "Expliquez les applications pratiques de l'intelligence artificielle générative.")
        model = request.get("model", "gemini-1.5-pro")
        
        # Initialiser le provider Gemini
        print(f"Initialisation du provider Gemini avec le modèle {model}")
        from .gemini_provider import GeminiProvider
        provider = GeminiProvider(model_name=model)
        
        # Vérifier que l'API fonctionne en envoyant une requête directe
        print(f"Envoi d'un prompt à Gemini: {prompt[:50]}...")
        response = await provider.generate_content(prompt=prompt)
        
        if "error" in response:
            return {"status": "error", "message": f"Erreur Gemini: {response['error']}"}
        
        return {
            "status": "success",
            "model": model,
            "prompt": prompt,
            "response": response["text"]
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Erreur lors du test Gemini: {str(e)}"}

@app.post("/api/test-gemini-langchain", response_model=Dict[str, Any])
async def tester_gemini_langchain(request: Dict[str, Any], api_key: str = Depends(verify_api_key)):
    """Route de test pour Google Gemini avec LangChain sans utiliser LangGraph."""
    try:
        # Récupérer les paramètres de la requête
        system_prompt = request.get("system_prompt", "Tu es un expert en intelligence artificielle. Réponds de manière claire et concise.")
        user_prompt = request.get("user_prompt", "Décris en 3 phrases les principales applications de l'IA générative dans le domaine de l'éducation.")
        model = request.get("model", "gemini-1.5-pro")
        
        # Importer les modules nécessaires
        import os
        from langchain_core.messages import SystemMessage, HumanMessage
        from langchain_google_genai import ChatGoogleGenerativeAI
        import google.generativeai as genai
        
        # Configuration explicite du module google.generativeai
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return {"status": "error", "message": "Clé API GEMINI_API_KEY non définie"}
            
        print(f"Configuration de google.generativeai avec la clé API")
        genai.configure(api_key=api_key)
        
        # Créer le modèle LangChain
        print(f"Création du modèle LangChain avec le modèle: {model}")
        chat_model = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True,
            transport="rest"
        )
        
        # Créer les messages
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Envoyer la requête
        print(f"Envoi des messages à Gemini via LangChain")
        response = chat_model.invoke(messages)
        
        return {
            "status": "success",
            "model": model,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "response": response.content
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Erreur lors du test Gemini avec LangChain: {str(e)}"} 