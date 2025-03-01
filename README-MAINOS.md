# Mainos - Plateforme Intelligente de Création de Documents

![Logo Mainos](https://via.placeholder.com/200x80?text=Mainos)

Mainos est une plateforme évoluée de création de documents intelligents, adaptée à différents besoins professionnels. Construite sur la base du projet Open Deep Research, Mainos utilise l'intelligence artificielle pour générer des documents de haute qualité, personnalisés selon le type, le ton et le format souhaités.

## Caractéristiques principales

- **Multiples types de documents** : Analyses de marché, rapports de risque, newsletters, cours, analyses SWOT, business plans et plus encore
- **Personnalisation avancée** : Ton (professionnel, académique, informel), longueur et format adaptés à vos besoins
- **Exports multi-formats** : Markdown, PDF, PowerPoint, Word et HTML
- **Benchmark qualité** : Évaluation automatique de la qualité par comparaison avec des exemples professionnels
- **Intégrations externes** : Exportation directe vers Notion, Google Docs, Slack et d'autres plateformes

## Installation

### Prérequis

- Python 3.10 ou supérieur
- pip (gestionnaire de paquets Python)

### Installation des dépendances

```bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate  # Linux/Mac
# ou
venv\\Scripts\\activate  # Windows

# Installer les dépendances
pip install -e .

# Installer les dépendances optionnelles pour les exports
pip install weasyprint python-pptx python-docx markdown
```

### Configuration des clés API

Créez un fichier `.env` à la racine du projet avec les clés API nécessaires :

```
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
TAVILY_API_KEY=your-tavily-api-key
MAINOS_API_KEY=your-mainos-api-key  # Clé pour l'authentification des clients
```

## Utilisation

### Lancement de l'API

```bash
# Activer l'environnement virtuel si ce n'est pas déjà fait
source venv/bin/activate

# Lancer l'API Mainos
python -m src.open_deep_research --mode api --reload
```

L'API sera disponible à l'adresse `http://127.0.0.1:8080`

### Documentation de l'API

La documentation interactive de l'API est disponible à l'adresse `http://127.0.0.1:8080/docs`

### Exemples d'utilisation

#### Création d'un rapport

```bash
curl -X POST http://localhost:8080/api/rapport \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-mainos-api-key" \
  -d '{
    "topic": "Impact de l'intelligence artificielle sur le marché du travail",
    "type_rapport": "analyse_marche",
    "ton": "professionnel",
    "longueur": "detaillee",
    "format_sortie": ["markdown", "pdf"],
    "benchmark_qualite": true
  }'
```

#### Récupération d'un rapport

```bash
curl -X GET http://localhost:8080/api/rapport/votre-report-id \
  -H "X-API-Key: your-mainos-api-key"
```

#### Téléchargement d'un rapport dans un format spécifique

```bash
curl -X GET http://localhost:8080/api/rapport/votre-report-id/download?format=pdf \
  -H "X-API-Key: your-mainos-api-key" \
  -o rapport.pdf
```

## Types de rapports disponibles

### Analyse de marché

Un examen détaillé d'un marché spécifique, incluant les tendances, les acteurs clés, la segmentation, les opportunités et les prévisions.

### Rapport de risque

Une évaluation approfondie des risques associés à un sujet, incluant l'identification, l'analyse et les stratégies d'atténuation.

### Newsletter

Une synthèse informative et engageante des actualités et développements récents sur un sujet spécifique.

### Cours

Un plan de cours structuré avec objectifs d'apprentissage, concepts clés, exemples pratiques et ressources complémentaires.

### Analyse SWOT

Une analyse des forces, faiblesses, opportunités et menaces, avec des recommandations stratégiques.

### Business Plan

Un plan d'affaires complet incluant la description de l'entreprise, l'analyse de marché, les stratégies et les projections financières.

### Étude compétitive

Une analyse détaillée de la concurrence, incluant des profils des concurrents, des comparaisons et des recommandations stratégiques.

## Options de personnalisation

### Tons disponibles

- **Professionnel** : Style formel adapté au contexte d'entreprise
- **Académique** : Style rigoureux avec méthodologie et références
- **Informatif** : Style clair et explicatif, axé sur la transmission d'information
- **Conversationnel** : Style plus décontracté et accessible
- **Prudent** : Style mesuré, présentant les nuances et incertitudes
- **Optimiste** : Style positif, mettant en avant les opportunités
- **Pédagogique** : Style didactique, facilitant l'apprentissage
- **Analytique** : Style centré sur l'analyse des données et des tendances

### Longueurs disponibles

- **Courte** : Synthèse concise des points essentiels
- **Moyenne** : Traitement équilibré avec développement modéré
- **Détaillée** : Analyse approfondie et exhaustive

### Formats de sortie

- Markdown (`.md`)
- PDF (`.pdf`)
- PowerPoint (`.pptx`)
- Word (`.docx`)
- HTML (`.html`)

## Architecture technique

Mainos est construit sur une architecture moderne utilisant:

- **FastAPI** pour l'API REST
- **LangGraph** pour l'orchestration des flux de travail
- **LangChain** pour les interactions avec les modèles de langage
- **Tavily/Perplexity** pour les recherches web

La plateforme utilise une approche modulaire qui permet d'adapter le traitement selon le type de document demandé.

## Contribuer

Les contributions sont les bienvenues! Consultez notre guide de contribution [CONTRIBUTING.md](CONTRIBUTING.md) pour plus d'informations.

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Contact

Pour toute question ou suggestion, contactez-nous à [email@example.com](mailto:email@example.com). 