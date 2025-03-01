#!/usr/bin/env python3
import os
import sys
import asyncio
from src.open_deep_research.gemini_provider import GeminiProvider

# Définir la clé API Gemini directement dans l'environnement
os.environ["GEMINI_API_KEY"] = "AIzaSyBmaunRUr8eI1BcXTxg_BvkBsks9W2eI5I"

def test_gemini_langchain():
    """Test de l'intégration avec LangChain."""
    print("\n=== TEST INTÉGRATION LANGCHAIN AVEC GEMINI ===")
    
    try:
        provider = GeminiProvider(model_name="gemini-1.5-pro")
        model = provider.get_langchain_model()
        
        print(f"Type du modèle LangChain: {type(model).__name__}")
        
        # Test simple
        prompt = "Expliquez brièvement l'importance de l'intelligence artificielle dans l'éducation."
        print(f"Envoi du prompt: '{prompt}'")
        
        response = model.invoke(prompt)
        print(f"Type de réponse: {type(response)}")
        print(f"Réponse obtenue: {response}")
        
        print("Test réussi!")
        return True
    except Exception as e:
        print(f"Erreur lors du test: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_gemini_langchain() 