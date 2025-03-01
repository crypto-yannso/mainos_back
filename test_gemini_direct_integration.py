#!/usr/bin/env python3
import os
import sys
from langchain_core.messages import SystemMessage, HumanMessage

# Définir la clé API Gemini
os.environ["GEMINI_API_KEY"] = "AIzaSyBmaunRUr8eI1BcXTxg_BvkBsks9W2eI5I"

def test_gemini_with_langchain():
    """Test direct de l'intégration Google Gemini avec LangChain"""
    print("\n=== TEST DIRECT GOOGLE GEMINI AVEC LANGCHAIN ===")
    
    try:
        # Importer les modules nécessaires
        print("Importation des modules nécessaires...")
        from langchain_google_genai import ChatGoogleGenerativeAI
        import google.generativeai as genai
        
        # Configuration explicite du module google.generativeai
        api_key = os.environ["GEMINI_API_KEY"]
        print(f"Configuration de google.generativeai avec la clé API: {api_key[:5]}...{api_key[-5:]}")
        genai.configure(api_key=api_key)
        
        # Créer le modèle LangChain
        model_name = "gemini-1.5-pro"
        print(f"Création du modèle LangChain avec le modèle: {model_name}")
        model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True,
            transport="rest"  # Utiliser REST au lieu de gRPC pour éviter les problèmes d'ADC
        )
        print(f"Modèle LangChain créé: {type(model).__name__}")
        
        # Tester avec un message système et un message humain
        messages = [
            SystemMessage(content="Tu es un expert en intelligence artificielle. Réponds de manière claire et concise."),
            HumanMessage(content="Décris en 3 phrases les principales applications de l'IA générative dans le domaine de l'éducation.")
        ]
        
        print(f"Envoi des messages à Gemini...")
        response = model.invoke(messages)
        
        print(f"Type de réponse: {type(response)}")
        print("\nContenu de la réponse:")
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
    test_gemini_with_langchain() 