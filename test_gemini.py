#!/usr/bin/env python3

import os
import requests
import json
import asyncio
from src.open_deep_research.gemini_provider import GeminiProvider

# Définir la clé API Gemini directement dans l'environnement
os.environ["GEMINI_API_KEY"] = "AIzaSyBmaunRUr8eI1BcXTxg_BvkBsks9W2eI5I"

async def test_gemini_direct():
    """Test direct d'un appel à l'API Gemini."""
    print("\n=== TEST DIRECT API GEMINI ===")
    provider = GeminiProvider()
    prompt = "Expliquez les applications pratiques de l'intelligence artificielle dans le secteur de la santé."
    print(f"Envoi du prompt à Gemini: '{prompt[:50]}...'")
    
    response = await provider.generate_content(prompt)
    
    if "error" in response:
        print(f"Erreur: {response['error']}")
        return None
        
    print(f"Réponse de Gemini ({len(response['text'])} caractères):")
    print("-" * 50)
    output_text = response['text']
    print(output_text[:500] + "..." if len(output_text) > 500 else output_text)
    print("-" * 50)
    return response

def test_mainos_api_with_gemini():
    """Test d'intégration avec l'API Mainos en utilisant Gemini."""
    print("\n=== TEST INTÉGRATION API MAINOS AVEC GEMINI ===")
    try:
        # Charger la requête depuis le fichier JSON
        with open("gemini_request.json", "r") as f:
            payload = json.load(f)
        
        # S'assurer que Google Gemini est bien configuré dans la requête
        payload["options_specifiques"]["planner_provider"] = "google_genai"
        payload["options_specifiques"]["planner_model"] = "gemini-1.5-pro"
        payload["options_specifiques"]["writer_provider"] = "google_genai"
        payload["options_specifiques"]["writer_model"] = "gemini-1.5-pro"
        
        print(f"Envoi de la requête à l'API Mainos:\n{json.dumps(payload, indent=2)[:200]}...")
        
        # Envoyer la requête à l'API Mainos
        response = requests.post(
            "http://localhost:8080/api/rapport",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "GUWWeHjgIRjLf3SSH17oA8CFz11eBoMWb3uuMvlWYyY"
            },
            json=payload
        )
        
        # Vérifier et afficher la réponse
        if response.status_code == 200:
            print(f"Succès! Réponse de l'API Mainos: {response.json()}")
        else:
            print(f"Erreur! Statut: {response.status_code}, Réponse: {response.text}")
        
        return response
    
    except Exception as e:
        print(f"Une erreur s'est produite lors du test: {str(e)}")
        return None

async def main():
    # Test direct de l'API Gemini
    gemini_response = await test_gemini_direct()
    
    # Test d'intégration avec l'API Mainos
    mainos_response = test_mainos_api_with_gemini()
    
    # Afficher le résumé
    print("\n=== RÉSUMÉ DES TESTS ===")
    print(f"Test direct Gemini: {'Succès' if gemini_response and 'text' in gemini_response else 'Échec'}")
    print(f"Test API Mainos: {'Succès' if mainos_response and mainos_response.status_code == 200 else 'Échec'}")

if __name__ == "__main__":
    asyncio.run(main()) 