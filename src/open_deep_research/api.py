from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from .graph import graph
import uuid
import asyncio

app = FastAPI(title="Open Deep Research API")

# Structure de la demande de recherche
class ResearchRequest(BaseModel):
    topic: str

# Structure de la réponse
class ResearchResponse(BaseModel):
    run_id: str
    status: str
    message: str

# Stockage en mémoire des tâches et résultats
tasks = {}
results = {}

@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API Open Deep Research"}

@app.post("/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    run_id = str(uuid.uuid4())
    
    # Définir la fonction pour exécuter le graphe en arrière-plan
    async def run_graph():
        try:
            result = await graph.ainvoke({"topic": request.topic})
            results[run_id] = {"status": "completed", "result": result}
            tasks[run_id] = "completed"
        except Exception as e:
            results[run_id] = {"status": "failed", "error": str(e)}
            tasks[run_id] = "failed"
    
    # Ajouter la tâche en arrière-plan
    background_tasks.add_task(run_graph)
    tasks[run_id] = "running"
    
    return {
        "run_id": run_id,
        "status": "running",
        "message": "Recherche démarrée"
    }

@app.get("/research/{run_id}", response_model=Dict[str, Any])
async def get_research_status(run_id: str):
    if run_id not in tasks:
        raise HTTPException(status_code=404, detail="Recherche non trouvée")
    
    status = tasks[run_id]
    
    if status == "completed":
        return {
            "status": status,
            "result": results.get(run_id, {}).get("result", {})
        }
    elif status == "failed":
        return {
            "status": status,
            "error": results.get(run_id, {}).get("error", "Une erreur inconnue s'est produite")
        }
    else:
        return {
            "status": status,
            "message": "Recherche en cours"
        } 