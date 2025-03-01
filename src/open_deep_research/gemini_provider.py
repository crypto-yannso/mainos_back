import os
import json
import requests
import sys
from typing import Dict, Any, List, Optional

class GeminiProvider:
    """Classe pour interagir avec l'API Gemini de Google"""
    
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        """Initialise le fournisseur Gemini avec le modèle spécifié"""
        print(f"Initialisation de GeminiProvider avec le modèle: {model_name}")
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("ERREUR: La clé API GEMINI_API_KEY n'est pas définie dans les variables d'environnement", file=sys.stderr)
            raise ValueError("La clé API GEMINI_API_KEY n'est pas définie dans les variables d'environnement")
        else:
            print(f"Clé API Gemini trouvée: {self.api_key[:5]}...{self.api_key[-5:]}")
        
        self.model_name = model_name
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
    
    async def generate_content(self, prompt: str, temperature: float = 0.7, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Génère du contenu avec Gemini à partir d'un prompt"""
        
        # Construction de la requête
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        # Ajout des paramètres optionnels
        generation_config = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens
        
        if generation_config:
            payload["generationConfig"] = generation_config
        
        # Ajout de la clé API comme paramètre d'URL
        url = f"{self.base_url}?key={self.api_key}"
        
        # Envoi de la requête
        try:
            print(f"Envoi d'une requête à l'API Gemini: {url[:60]}...")
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload)
            )
            response.raise_for_status()  # Lève une exception si la requête a échoué
            
            # Traitement de la réponse
            response_data = response.json()
            
            # Extraction du texte généré
            if "candidates" in response_data and len(response_data["candidates"]) > 0:
                candidate = response_data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return {"text": parts[0]["text"]}
            
            # En cas de format de réponse inattendu
            print(f"Format de réponse inattendu: {json.dumps(response_data)[:200]}...", file=sys.stderr)
            return {"text": "Erreur: Format de réponse inattendu", "raw_response": response_data}
            
        except Exception as e:
            print(f"Erreur lors de l'appel à l'API Gemini: {e}", file=sys.stderr)
            return {"error": str(e)}
    
    async def generate_with_system_prompt(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> Dict[str, Any]:
        """Génère du contenu avec un prompt système et un prompt utilisateur"""
        
        # Combiner les prompts pour Gemini (qui ne supporte pas nativement le concept de "system prompt")
        combined_prompt = f"Instructions système: {system_prompt}\n\nRequête utilisateur: {user_prompt}"
        
        return await self.generate_content(combined_prompt, temperature)
    
    def get_langchain_model(self):
        """Retourne un modèle LangChain compatible avec Google Gemini"""
        try:
            print("Tentative d'importation des modules langchain-google-genai et google-generativeai...")
            from langchain_google_genai import ChatGoogleGenerativeAI
            import google.generativeai as genai
            
            print(f"Configuration de l'API Gemini avec la clé: {self.api_key[:5]}...{self.api_key[-5:]}")
            # Configuration explicite avec la clé API pour éviter l'utilisation des identifiants par défaut
            genai.configure(api_key=self.api_key)
            
            print(f"Création du modèle LangChain avec le modèle: {self.model_name}")
            # Création du modèle LangChain
            model = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,  # Passage explicite de la clé API
                temperature=0.7,
                convert_system_message_to_human=True,  # Important pour les prompts système
                transport="rest"  # Utiliser REST au lieu de gRPC pour éviter les problèmes d'ADC
            )
            
            print("Modèle LangChain créé avec succès")
            return model
        except ImportError as e:
            print(f"Erreur d'importation: {e}", file=sys.stderr)
            raise ImportError(
                "Les packages langchain-google-genai et google-generativeai sont nécessaires. "
                "Installez-les avec: pip install -U langchain-google-genai google-generativeai"
            )
        except Exception as e:
            print(f"Erreur inattendue lors de la création du modèle LangChain: {e}", file=sys.stderr)
            raise 