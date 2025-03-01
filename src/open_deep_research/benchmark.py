import os
import json
from typing import Dict, Any, List, Optional
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

from .mainos_types import TypeRapport

class QualityBenchmark:
    """Classe pour évaluer la qualité des rapports générés en les comparant à des exemples de référence"""
    
    def __init__(self, type_rapport: str, model_provider: str = "openai", model_name: str = "gpt-4o"):
        """
        Initialise le benchmark pour un type de rapport spécifique
        
        Args:
            type_rapport: Le type de rapport à évaluer
            model_provider: Le fournisseur du modèle d'évaluation
            model_name: Le nom du modèle d'évaluation
        """
        self.type_rapport = type_rapport
        self.model_provider = model_provider
        self.model_name = model_name
        self.examples = self._load_examples()
        self.evaluation_model = init_chat_model(
            model=model_name,
            model_provider=model_provider,
            temperature=0
        )
    
    def _load_examples(self) -> List[Dict[str, Any]]:
        """Charge les exemples de référence pour le type de rapport spécifié"""
        examples_path = os.path.join(
            os.path.dirname(__file__),
            "benchmark_examples",
            f"{self.type_rapport}.json"
        )
        
        # Si le fichier n'existe pas, retourner une liste vide
        if not os.path.exists(examples_path):
            # Créer un exemple par défaut pour ce type
            default_examples = self._create_default_examples()
            
            # Créer le répertoire s'il n'existe pas
            os.makedirs(os.path.dirname(examples_path), exist_ok=True)
            
            # Enregistrer l'exemple par défaut
            with open(examples_path, "w") as f:
                json.dump(default_examples, f, indent=2)
            
            return default_examples
        
        # Charger les exemples depuis le fichier
        with open(examples_path, "r") as f:
            return json.load(f)
    
    def _create_default_examples(self) -> List[Dict[str, Any]]:
        """Crée des exemples par défaut pour le type de rapport spécifié"""
        # Exemples par défaut selon le type de rapport
        if self.type_rapport == TypeRapport.ANALYSE_MARCHE:
            return [{
                "title": "Analyse du marché des véhicules électriques",
                "sections": ["Introduction", "Tendances actuelles", "Acteurs clés", "Prévisions"],
                "quality_criteria": [
                    "Utilisation de données récentes",
                    "Analyse des concurrents",
                    "Prévisions chiffrées",
                    "Citations de sources crédibles"
                ]
            }]
        elif self.type_rapport == TypeRapport.ANALYSE_SWOT:
            return [{
                "title": "Analyse SWOT de Tesla",
                "sections": ["Forces", "Faiblesses", "Opportunités", "Menaces"],
                "quality_criteria": [
                    "Facteurs internes et externes bien distingués",
                    "Analyse équilibrée des 4 catégories",
                    "Recommandations stratégiques",
                    "Priorisation des facteurs"
                ]
            }]
        # Ajouter d'autres types de rapports au besoin
        return [{
            "title": "Exemple de rapport",
            "sections": ["Introduction", "Développement", "Conclusion"],
            "quality_criteria": [
                "Structure cohérente",
                "Contenu factuel",
                "Sources citées",
                "Clarté du propos"
            ]
        }]
    
    async def evaluate(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Évalue la qualité du contenu généré par comparaison avec les exemples de référence
        
        Args:
            content: Le contenu du rapport à évaluer
            
        Returns:
            Un dictionnaire contenant le score et les recommandations
        """
        # Construire le prompt d'évaluation
        evaluation_prompt = self._build_evaluation_prompt(content)
        
        # Structure pour la sortie de l'évaluation
        evaluation_output = {
            "score": {
                "overall": 0,
                "criteria": {}
            },
            "recommendations": []
        }
        
        # Obtenir l'évaluation du modèle
        result = await self.evaluation_model.ainvoke([
            SystemMessage(content=evaluation_prompt),
            HumanMessage(content="Évaluez ce rapport selon les critères fournis.")
        ])
        
        # Analyser le résultat et extraire le score et les recommandations
        try:
            # Tenter d'extraire les informations structurées de la réponse
            response_text = result.content
            
            # Extraire le score global (chiffre entre 0 et 10)
            import re
            score_match = re.search(r"Score global\s*:\s*(\d+(?:\.\d+)?)", response_text)
            if score_match:
                evaluation_output["score"]["overall"] = float(score_match.group(1))
            
            # Extraire les recommandations (lignes commençant par - ou *)
            recommendations = re.findall(r"[-*]\s*([^\n]+)", response_text)
            evaluation_output["recommendations"] = recommendations
            
            # Extraire les scores par critère si présents
            criteria_scores = re.findall(r"([^:]+):\s*(\d+(?:\.\d+)?)/10", response_text)
            for criterion, score in criteria_scores:
                evaluation_output["score"]["criteria"][criterion.strip()] = float(score)
        
        except Exception as e:
            evaluation_output["error"] = str(e)
        
        return evaluation_output
    
    def _build_evaluation_prompt(self, content: Dict[str, Any]) -> str:
        """
        Construit le prompt d'évaluation pour le modèle
        
        Args:
            content: Le contenu du rapport à évaluer
            
        Returns:
            Le prompt d'évaluation
        """
        # Extraire les critères de qualité des exemples
        quality_criteria = []
        for example in self.examples:
            if "quality_criteria" in example:
                quality_criteria.extend(example["quality_criteria"])
        
        # Éliminer les doublons
        quality_criteria = list(set(quality_criteria))
        
        # Construire le prompt
        prompt = f"""
        Vous êtes un expert en évaluation de documents professionnels, spécialisé dans les {self.type_rapport}.
        
        Votre tâche est d'évaluer la qualité du rapport suivant selon les critères spécifiés.
        Donnez un score de 0 à 10 pour chaque critère et un score global.
        
        # Rapport à évaluer
        
        Titre: {content.get('title', 'Sans titre')}
        
        Contenu:
        {json.dumps(content, indent=2, ensure_ascii=False)}
        
        # Critères d'évaluation
        
        {chr(10).join([f"- {criterion}" for criterion in quality_criteria])}
        
        # Format de votre évaluation
        
        Veuillez structurer votre évaluation ainsi:
        
        Score global: [0-10]
        
        Évaluation par critère:
        - Critère 1: [score]/10
        - Critère 2: [score]/10
        ...
        
        Recommandations d'amélioration:
        - Recommandation 1
        - Recommandation 2
        ...
        
        """
        
        return prompt 