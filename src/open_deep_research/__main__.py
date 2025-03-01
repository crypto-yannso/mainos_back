#!/usr/bin/env python3
"""
Point d'entrée principal pour l'application Mainos
"""

import argparse
import os
import sys
import uvicorn

def main():
    """
    Fonction principale pour lancer l'application
    """
    parser = argparse.ArgumentParser(
        description="Mainos - Plateforme de création de rapports intelligents"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["api", "graph"],
        default="api",
        help="Mode de lancement: 'api' pour l'API complète, 'graph' pour exposer directement le graphe"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Hôte sur lequel lancer le serveur"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port sur lequel lancer le serveur"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Activer le rechargement automatique en cas de modification des fichiers"
    )
    
    args = parser.parse_args()
    
    # S'assurer que PYTHONPATH contient le répertoire du projet
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    
    # Configurer l'application à lancer
    if args.mode == "api":
        app_module = "src.open_deep_research.mainos_api:app"
        print(f"Lancement de l'API Mainos sur http://{args.host}:{args.port}")
    else:
        app_module = "src.open_deep_research.mainos_graph:mainos_graph"
        print(f"Exposition du graphe Mainos sur http://{args.host}:{args.port}")
    
    # Lancer l'application avec uvicorn
    uvicorn.run(
        app_module,
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main() 