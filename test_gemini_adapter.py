#!/usr/bin/env python3
import os
import sys
import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from src.open_deep_research.gemini_adapter import GeminiAdapter

# Définir la clé API Gemini directement dans l'environnement
os.environ["GEMINI_API_KEY"] = "AIzaSyBmaunRUr8eI1BcXTxg_BvkBsks9W2eI5I"

def test_gemini_adapter():
    """Test de notre adaptateur GeminiAdapter."""
    print("\n=== TEST GEMINI ADAPTER ===")
    
    try:
        adapter = GeminiAdapter(model_name="gemini-1.5-pro", temperature=0.7)
        
        # Test avec un message système et un message humain
        messages = [
            SystemMessage(content="Tu es un expert en intelligence artificielle. Réponds de manière claire et concise."),
            HumanMessage(content="Quels sont les principaux défis éthiques de l'intelligence artificielle aujourd'hui?")
        ]
        
        print(f"Messages envoyés: {len(messages)}")
        print(f"1. {messages[0].type}: {messages[0].content[:50]}...")
        print(f"2. {messages[1].type}: {messages[1].content[:50]}...")
        
        response = adapter.invoke(messages)
        
        print(f"\nType de réponse: {type(response)}")
        print(f"Contenu de la réponse:")
        print("-" * 80)
        print(response.content)
        print("-" * 80)
        
        print("Test réussi!")
        return True
    except Exception as e:
        print(f"Erreur lors du test: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_gemini_adapter() 