#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exemple d'utilisation directe de Mainos via son API Python.
Ce script montre comment générer différents types de rapports
et utiliser les fonctionnalités principales sans passer par l'API HTTP.
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au PATH pour l'import
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.open_deep_research.mainos_graph import mainos_invoke
from src.open_deep_research.mainos_types import (
    FormatSortie,
    LongueurRapport,
    MainosState,
    PlateformeIntegration,
    TonRapport,
    TypeRapport,
)
from src.open_deep_research.export import exporter_rapport

# Charger les variables d'environnement si nécessaire
from dotenv import load_dotenv
load_dotenv()

def generer_rapport(
    sujet: str,
    type_rapport: TypeRapport,
    ton: TonRapport = TonRapport.PROFESSIONNEL,
    longueur: LongueurRapport = LongueurRapport.MOYENNE,
    format_sortie: FormatSortie = FormatSortie.MARKDOWN,
    benchmark: bool = False,
):
    """
    Génère un rapport en utilisant le graphe Mainos directement.
    
    Args:
        sujet: Le sujet du rapport
        type_rapport: Le type de rapport à générer
        ton: Le ton à utiliser
        longueur: La longueur souhaitée
        format_sortie: Le format de sortie du rapport
        benchmark: Si True, effectue une évaluation qualité
        
    Returns:
        Le rapport généré et les métadonnées associées
    """
    print(f"Génération d'un rapport de type {type_rapport.value} sur le sujet: {sujet}")
    
    # Créer l'état initial
    initial_state = MainosState(
        topic=sujet,
        type_rapport=type_rapport,
        ton=ton,
        longueur=longueur,
        format_sortie=[format_sortie],
        sections=[],
        benchmark_qualite=benchmark,
        rapport_complet="",
        resultats_benchmark={},
    )
    
    # Invoquer le graphe
    try:
        resultat = mainos_invoke(initial_state)
        
        print(f"✅ Rapport généré avec succès!")
        print(f"Longueur du rapport: {len(resultat.rapport_complet)} caractères")
        
        if benchmark and resultat.resultats_benchmark:
            print("\n=== Résultats du benchmark ===")
            for critere, score in resultat.resultats_benchmark.items():
                print(f"{critere}: {score}/10")
            print("===========================\n")
        
        # Sauvegarder le rapport
        chemin_sortie = f"rapport_{type_rapport.value}_{format_sortie.value.lower()}"
        with open(f"{chemin_sortie}.{format_sortie.value.lower()}", "w", encoding="utf-8") as f:
            f.write(resultat.rapport_complet)
        
        print(f"Rapport sauvegardé sous: {chemin_sortie}.{format_sortie.value.lower()}")
        
        return resultat
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport: {str(e)}")
        raise


def main():
    """Fonction principale avec exemples d'utilisation."""
    
    # Exemple 1: Générer une analyse de marché
    analyse = generer_rapport(
        sujet="Le marché des véhicules électriques en Europe",
        type_rapport=TypeRapport.ANALYSE_MARCHE,
        ton=TonRapport.ANALYTIQUE,
        longueur=LongueurRapport.MOYENNE,
        format_sortie=FormatSortie.MARKDOWN,
        benchmark=True,
    )
    
    # Attendre la confirmation de l'utilisateur pour continuer
    input("\nAppuyez sur Entrée pour continuer avec l'exemple suivant...\n")
    
    # Exemple 2: Générer un rapport de risque
    risque = generer_rapport(
        sujet="Risques cybersécurité dans le secteur bancaire",
        type_rapport=TypeRapport.RAPPORT_RISQUE,
        ton=TonRapport.PRUDENT,
        longueur=LongueurRapport.DETAILLEE,
        format_sortie=FormatSortie.MARKDOWN,
    )
    
    # Exemple 3: Convertir un rapport existant vers un autre format
    if analyse and hasattr(analyse, 'rapport_complet'):
        print("\nConversion du rapport d'analyse de marché en PDF...")
        try:
            # Exemple de conversion en PDF (nécessite weasyprint)
            from src.open_deep_research.export import convertir_markdown_pdf
            
            pdf_path = "rapport_analyse_marche.pdf"
            convertir_markdown_pdf(analyse.rapport_complet, pdf_path)
            print(f"Rapport converti en PDF: {pdf_path}")
        except ImportError:
            print("Module weasyprint non disponible. Conversion en PDF ignorée.")
    
    print("\nExemple d'utilisation de Mainos terminé!")


if __name__ == "__main__":
    main() 