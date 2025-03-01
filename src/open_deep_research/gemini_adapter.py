import os
import json
import sys
from typing import Any, Dict, List, Optional, Union

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from pydantic import Field, PrivateAttr

from .gemini_provider import GeminiProvider

class GeminiAdapter(BaseChatModel):
    """Adaptateur pour intégrer GeminiProvider avec l'architecture LangGraph"""
    
    model_name: str = Field(default="gemini-1.5-pro")
    temperature: float = Field(default=0.7)
    
    _provider: GeminiProvider = PrivateAttr()
    
    def __init__(self, model_name: str = "gemini-1.5-pro", temperature: float = 0.7, **kwargs):
        """Initialise l'adaptateur avec une instance de GeminiProvider"""
        super().__init__(model_name=model_name, temperature=temperature, **kwargs)
        
        print(f"Initialisation de GeminiAdapter pour le modèle {model_name}")
        self._provider = GeminiProvider(model_name=model_name)
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """Génère une réponse à partir des messages fournis.
        Cette méthode est utilisée par la classe BaseChatModel.
        """
        import asyncio
        
        print(f"Génération de réponse pour {len(messages)} messages")
        # Préparer le prompt en fonction des messages
        system_prompt = ""
        user_prompt = ""
        
        for message in messages:
            if isinstance(message, SystemMessage):
                system_prompt += message.content + "\n"
            elif isinstance(message, HumanMessage):
                user_prompt += message.content + "\n"
            elif isinstance(message, AIMessage):
                # Ignorer les messages AI pour l'instant
                pass
        
        # Utiliser generate_with_system_prompt si nous avons un prompt système
        if system_prompt:
            print(f"Utilisation de generate_with_system_prompt (système: {len(system_prompt)} caractères, utilisateur: {len(user_prompt)} caractères)")
            response_coroutine = self._provider.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature
            )
        else:
            print(f"Utilisation de generate_content (prompt: {len(user_prompt)} caractères)")
            response_coroutine = self._provider.generate_content(
                prompt=user_prompt,
                temperature=self.temperature
            )
        
        # Exécuter la coroutine de manière synchrone
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Si aucun event loop n'est disponible dans ce thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(response_coroutine)
        
        # Vérifier si une erreur s'est produite
        if "error" in response:
            print(f"Erreur lors de l'appel à l'API Gemini: {response['error']}", file=sys.stderr)
            raise ValueError(f"Erreur lors de l'appel à l'API Gemini: {response['error']}")
        
        # Créer un AI message à partir de la réponse
        ai_message = AIMessage(content=response["text"])
        
        # Créer la structure de réponse attendue par LangChain
        from langchain_core.outputs import ChatGenerationChunk, ChatResult
        
        generation = ChatGenerationChunk(message=ai_message)
        result = ChatResult(generations=[generation])
        
        return result
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """Version asynchrone de _generate"""
        # Préparer le prompt en fonction des messages
        system_prompt = ""
        user_prompt = ""
        
        for message in messages:
            if isinstance(message, SystemMessage):
                system_prompt += message.content + "\n"
            elif isinstance(message, HumanMessage):
                user_prompt += message.content + "\n"
            elif isinstance(message, AIMessage):
                # Ignorer les messages AI pour l'instant
                pass
        
        # Utiliser generate_with_system_prompt si nous avons un prompt système
        if system_prompt:
            response = await self._provider.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.temperature
            )
        else:
            response = await self._provider.generate_content(
                prompt=user_prompt,
                temperature=self.temperature
            )
        
        # Vérifier si une erreur s'est produite
        if "error" in response:
            raise ValueError(f"Erreur lors de l'appel à l'API Gemini: {response['error']}")
        
        # Créer un AI message à partir de la réponse
        ai_message = AIMessage(content=response["text"])
        
        # Créer la structure de réponse attendue par LangChain
        from langchain_core.outputs import ChatGenerationChunk, ChatResult
        
        generation = ChatGenerationChunk(message=ai_message)
        result = ChatResult(generations=[generation])
        
        return result
    
    @property
    def _llm_type(self) -> str:
        return "gemini-adapter" 