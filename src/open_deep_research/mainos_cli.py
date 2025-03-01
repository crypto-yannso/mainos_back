#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Interface en ligne de commande pour Mainos.
Permet de générer des rapports, de les convertir dans différents formats
et de les intégrer avec différentes plateformes.
"""

import argparse
import json
import os
import sys
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

# Ajout du répertoire parent au chemin Python si nécessaire
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.open_deep_research.mainos_types import (
    FormatSortie,
    LongueurRapport,
    MainosState,
    PlateformeIntegration,
    TonRapport,
    TypeRapport,
)
from src.open_deep_research.mainos_graph import mainos_invoke
from src.open_deep_research.export import exporter_rapport, integrer_avec_plateforme
from src.open_deep_research.benchmark import QualityBenchmark

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()


class Actions(str, Enum):
    """Actions disponibles pour l'interface en ligne de commande."""
    GENERER = "generer"
    CONVERTIR = "convertir"
    INTEGRER = "integrer"
    BENCHMARK = "benchmark"
    LISTER_TYPES = "lister-types"


def parse_args():
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(description="Interface en ligne de commande Mainos pour la génération de rapports")
    
    parser.add_argument("action", type=Actions, choices=list(Actions), 
                      help="Action à effectuer")
    
    # Arguments pour la génération de rapports
    parser.add_argument("--sujet", "-s", type=str,
                      help="Sujet du rapport à générer")
    
    parser.add_argument("--type", "-t", type=str,
                      help=f"Type de rapport à générer. Utiliser '{Actions.LISTER_TYPES}' pour voir les types disponibles")
    
    parser.add_argument("--ton", type=str, default="professionnel",
                      help="Ton à utiliser pour le rapport (professionnel, academique, informatif, etc.)")
    
    parser.add_argument("--longueur", "-l", type=str, default="moyenne",
                      help="Longueur du rapport (courte, moyenne, detaillee)")
    
    parser.add_argument("--format", "-f", type=str, default="markdown",
                      help="Format de sortie (markdown, pdf, html, docx, pptx)")
    
    parser.add_argument("--fichier-entree", "-i", type=str,
                      help="Fichier d'entrée (pour convertir ou intégrer)")
    
    parser.add_argument("--fichier-sortie", "-o", type=str,
                      help="Chemin du fichier de sortie")
    
    parser.add_argument("--plateforme", "-p", type=str,
                      help="Plateforme d'intégration (notion, google_docs, slack, github)")
    
    parser.add_argument("--benchmark", "-b", action="store_true",
                      help="Évaluer la qualité du rapport généré")
    
    parser.add_argument("--metadata", "-m", type=json.loads, default="{}",
                      help='Métadonnées JSON, par exemple : \'{"title": "Mon rapport", "author": "Mainos"}\'')
    
    return parser.parse_args()


def lister_types():
    """Affiche la liste des types de rapports disponibles."""
    print("\n=== Types de rapports disponibles ===\n")
    
    for type_rapport in TypeRapport:
        print(f"- {type_rapport.value}: {type_rapport.name}")
    
    print("\n=== Tons disponibles ===\n")
    for ton in TonRapport:
        print(f"- {ton.value}: {ton.name}")
    
    print("\n=== Longueurs disponibles ===\n")
    for longueur in LongueurRapport:
        print(f"- {longueur.value}: {longueur.name}")
    
    print("\n=== Formats de sortie disponibles ===\n")
    for format_sortie in FormatSortie:
        print(f"- {format_sortie.value}: {format_sortie.name}")
    
    print("\n=== Plateformes d'intégration ===\n")
    for plateforme in PlateformeIntegration:
        print(f"- {plateforme.value}: {plateforme.name}")


def generer_rapport(
    sujet: str,
    type_rapport: str,
    ton: str = "professionnel",
    longueur: str = "moyenne",
    format_sortie: str = "markdown",
    fichier_sortie: Optional[str] = None,
    benchmark: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Génère un rapport avec les paramètres spécifiés.
    
    Args:
        sujet: Sujet du rapport
        type_rapport: Type de rapport
        ton: Ton à utiliser
        longueur: Longueur du rapport
        format_sortie: Format de sortie
        fichier_sortie: Chemin du fichier de sortie
        benchmark: Si True, évalue la qualité du rapport
        metadata: Métadonnées pour le rapport
        
    Returns:
        Un dictionnaire avec les informations sur le rapport généré
    """
    # Convertir les chaînes en énumérations
    try:
        type_enum = TypeRapport(type_rapport)
        ton_enum = TonRapport(ton)
        longueur_enum = LongueurRapport(longueur)
        format_enum = FormatSortie(format_sortie)
    except ValueError as e:
        print(f"Erreur: {e}")
        print("Utilisez 'lister-types' pour voir les valeurs disponibles.")
        sys.exit(1)
    
    # Afficher les informations sur la génération
    print(f"\n🚀 Génération d'un rapport de type '{type_enum.value}'")
    print(f"Sujet: {sujet}")
    print(f"Ton: {ton_enum.value}")
    print(f"Longueur: {longueur_enum.value}")
    print(f"Format: {format_enum.value}")
    print(f"Benchmark: {'Oui' if benchmark else 'Non'}")
    print("\nGénération en cours... Cela peut prendre quelques minutes.\n")
    
    # Créer l'état initial
    initial_state = MainosState(
        topic=sujet,
        type_rapport=type_enum,
        ton=ton_enum,
        longueur=longueur_enum,
        format_sortie=[format_enum],
        sections=[],
        benchmark_qualite=benchmark,
        rapport_complet="",
        resultats_benchmark={},
    )
    
    # Invoquer le graphe
    try:
        resultat = mainos_invoke(initial_state)
        
        print(f"\n✅ Rapport généré avec succès!")
        print(f"Longueur du rapport: {len(resultat.rapport_complet)} caractères")
        
        # Afficher les résultats du benchmark si demandé
        if benchmark and resultat.resultats_benchmark:
            print("\n=== Résultats du benchmark ===")
            for critere, score in resultat.resultats_benchmark.items():
                print(f"{critere}: {score}/10")
            print("===========================\n")
        
        # Déterminer le nom de fichier de sortie s'il n'est pas spécifié
        if not fichier_sortie:
            type_nom = type_enum.value.replace("_", "-")
            fichier_sortie = f"rapport_{type_nom}.{format_enum.value.lower()}"
        
        # Exporter le rapport
        chemin_sortie = exporter_rapport(
            resultat.rapport_complet, 
            format_enum, 
            fichier_sortie,
            metadata
        )
        
        print(f"📄 Rapport sauvegardé sous: {chemin_sortie}")
        
        return {
            "success": True,
            "file_path": chemin_sortie,
            "content_length": len(resultat.rapport_complet),
            "benchmark_results": resultat.resultats_benchmark if benchmark else {},
        }
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la génération du rapport: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


def convertir_rapport(
    fichier_entree: str,
    format_sortie: str,
    fichier_sortie: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convertit un rapport existant vers un autre format.
    
    Args:
        fichier_entree: Chemin du fichier d'entrée
        format_sortie: Format de sortie souhaité
        fichier_sortie: Chemin du fichier de sortie
        metadata: Métadonnées pour le document
        
    Returns:
        Un dictionnaire avec les informations sur la conversion
    """
    print(f"\n🔄 Conversion du fichier '{fichier_entree}' vers le format '{format_sortie}'")
    
    try:
        # Vérifier que le fichier d'entrée existe
        if not os.path.exists(fichier_entree):
            raise FileNotFoundError(f"Le fichier '{fichier_entree}' n'existe pas.")
        
        # Convertir le format de sortie en énumération
        try:
            format_enum = FormatSortie(format_sortie)
        except ValueError:
            print(f"Format non pris en charge: {format_sortie}")
            print("Formats disponibles:")
            for fmt in FormatSortie:
                print(f"- {fmt.value}")
            return {"success": False, "error": f"Format non pris en charge: {format_sortie}"}
        
        # Déterminer le nom de fichier de sortie s'il n'est pas spécifié
        if not fichier_sortie:
            base_name = os.path.splitext(os.path.basename(fichier_entree))[0]
            fichier_sortie = f"{base_name}.{format_enum.value.lower()}"
        
        # Lire le contenu du fichier d'entrée
        with open(fichier_entree, "r", encoding="utf-8") as f:
            contenu = f.read()
        
        # Exporter le rapport
        chemin_sortie = exporter_rapport(
            contenu, 
            format_enum, 
            fichier_sortie,
            metadata
        )
        
        print(f"📄 Rapport converti et sauvegardé sous: {chemin_sortie}")
        
        return {
            "success": True,
            "file_path": chemin_sortie,
            "original_file": fichier_entree,
        }
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la conversion du rapport: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


def integrer_rapport(
    fichier_entree: str,
    plateforme: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Intègre un rapport avec une plateforme externe.
    
    Args:
        fichier_entree: Chemin du fichier d'entrée
        plateforme: Plateforme d'intégration
        metadata: Métadonnées pour l'intégration
        
    Returns:
        Un dictionnaire avec les informations sur l'intégration
    """
    print(f"\n🔌 Intégration du fichier '{fichier_entree}' avec la plateforme '{plateforme}'")
    
    try:
        # Vérifier que le fichier d'entrée existe
        if not os.path.exists(fichier_entree):
            raise FileNotFoundError(f"Le fichier '{fichier_entree}' n'existe pas.")
        
        # Convertir la plateforme en énumération
        try:
            plateforme_enum = PlateformeIntegration(plateforme)
        except ValueError:
            print(f"Plateforme non prise en charge: {plateforme}")
            print("Plateformes disponibles:")
            for p in PlateformeIntegration:
                print(f"- {p.value}")
            return {"success": False, "error": f"Plateforme non prise en charge: {plateforme}"}
        
        # Déterminer le format de sortie en fonction de l'extension du fichier
        extension = os.path.splitext(fichier_entree)[1].lower().replace(".", "")
        try:
            format_enum = FormatSortie(extension) if extension in [f.value.lower() for f in FormatSortie] else FormatSortie.MARKDOWN
        except ValueError:
            format_enum = FormatSortie.MARKDOWN
        
        # Lire le contenu du fichier d'entrée
        with open(fichier_entree, "r", encoding="utf-8") as f:
            contenu = f.read()
        
        # Intégrer le rapport
        resultat = integrer_avec_plateforme(
            contenu,
            plateforme_enum,
            format_enum,
            None,  # credentials (normalement pris depuis les variables d'environnement)
            metadata
        )
        
        print(f"🔗 Rapport intégré avec succès!")
        if "url" in resultat:
            print(f"🌐 URL: {resultat['url']}")
        print(f"📊 Détails: {json.dumps(resultat, indent=2)}")
        
        return {
            "success": True,
            "integration_result": resultat,
            "original_file": fichier_entree,
        }
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'intégration du rapport: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


def evaluer_rapport(
    fichier_entree: str,
) -> Dict[str, Any]:
    """
    Évalue la qualité d'un rapport existant.
    
    Args:
        fichier_entree: Chemin du fichier à évaluer
        
    Returns:
        Un dictionnaire avec les résultats de l'évaluation
    """
    print(f"\n🔍 Évaluation de la qualité du rapport '{fichier_entree}'")
    
    try:
        # Vérifier que le fichier d'entrée existe
        if not os.path.exists(fichier_entree):
            raise FileNotFoundError(f"Le fichier '{fichier_entree}' n'existe pas.")
        
        # Lire le contenu du fichier d'entrée
        with open(fichier_entree, "r", encoding="utf-8") as f:
            contenu = f.read()
        
        # Créer un evaluateur de qualité
        evaluateur = QualityBenchmark()
        
        # Évaluer la qualité du rapport
        resultats = evaluateur.evaluate_report_quality(contenu)
        
        print("\n=== Résultats de l'évaluation ===")
        for critere, score in resultats.items():
            print(f"{critere}: {score}/10")
        print("===========================\n")
        
        # Calculer le score moyen
        score_moyen = sum(resultats.values()) / len(resultats)
        print(f"Score moyen: {score_moyen:.1f}/10")
        
        return {
            "success": True,
            "results": resultats,
            "average_score": score_moyen,
            "file": fichier_entree,
        }
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'évaluation du rapport: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


def main():
    """Point d'entrée principal."""
    # Analyser les arguments
    args = parse_args()
    
    # Exécuter l'action demandée
    if args.action == Actions.LISTER_TYPES:
        lister_types()
    
    elif args.action == Actions.GENERER:
        if not args.sujet or not args.type:
            print("Erreur: Les arguments --sujet et --type sont requis pour générer un rapport.")
            sys.exit(1)
        
        generer_rapport(
            sujet=args.sujet,
            type_rapport=args.type,
            ton=args.ton,
            longueur=args.longueur,
            format_sortie=args.format,
            fichier_sortie=args.fichier_sortie,
            benchmark=args.benchmark,
            metadata=args.metadata,
        )
    
    elif args.action == Actions.CONVERTIR:
        if not args.fichier_entree or not args.format:
            print("Erreur: Les arguments --fichier-entree et --format sont requis pour convertir un rapport.")
            sys.exit(1)
        
        convertir_rapport(
            fichier_entree=args.fichier_entree,
            format_sortie=args.format,
            fichier_sortie=args.fichier_sortie,
            metadata=args.metadata,
        )
    
    elif args.action == Actions.INTEGRER:
        if not args.fichier_entree or not args.plateforme:
            print("Erreur: Les arguments --fichier-entree et --plateforme sont requis pour intégrer un rapport.")
            sys.exit(1)
        
        integrer_rapport(
            fichier_entree=args.fichier_entree,
            plateforme=args.plateforme,
            metadata=args.metadata,
        )
    
    elif args.action == Actions.BENCHMARK:
        if not args.fichier_entree:
            print("Erreur: L'argument --fichier-entree est requis pour évaluer un rapport.")
            sys.exit(1)
        
        evaluer_rapport(
            fichier_entree=args.fichier_entree,
        )


if __name__ == "__main__":
    main() 