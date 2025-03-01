# Dockerisation de l'Application Mainos

Ce document explique comment utiliser Docker pour déployer l'application Mainos.

## Prérequis

- Docker installé sur votre machine
- Docker Compose installé sur votre machine

## Configuration

1. Créez un fichier `.env` à la racine du projet basé sur le fichier `.env.example` :

```bash
cp .env.example .env
```

2. Modifiez le fichier `.env` pour y ajouter vos clés API et autres configurations :

```
OPENAI_API_KEY=votre_clé_openai
ANTHROPIC_API_KEY=votre_clé_anthropic
TAVILY_API_KEY=votre_clé_tavily
PERPLEXITY_API_KEY=votre_clé_perplexity
SEARCH_API=perplexity
MAINOS_API_KEY=votre_clé_mainos
GEMINI_API_KEY=votre_clé_gemini
```

## Construction et lancement

### Avec Docker Compose (recommandé)

1. Construisez et lancez l'application avec Docker Compose :

```bash
docker-compose up -d
```

2. Pour arrêter l'application :

```bash
docker-compose down
```

### Avec Docker directement

1. Construisez l'image Docker :

```bash
docker build -t mainos-api .
```

2. Lancez un conteneur basé sur cette image :

```bash
docker run -p 8080:8080 --env-file .env -d mainos-api
```

## Accéder à l'application

Une fois l'application lancée, elle sera accessible à l'adresse suivante :

- API Mainos : http://localhost:8080

## Logs et débogage

Pour voir les logs de l'application en temps réel :

```bash
docker-compose logs -f
```

## Personnalisation

Vous pouvez modifier le fichier `docker-compose.yml` pour ajuster les paramètres selon vos besoins, comme :
- Changer le port exposé
- Ajouter des volumes supplémentaires
- Modifier les variables d'environnement

## Considérations pour la production

Pour un déploiement en production, envisagez ces ajustements supplémentaires :

1. Utilisez un serveur proxy inverse comme Nginx pour gérer le trafic entrant
2. Configurez des limites de ressources (CPU, mémoire) appropriées
3. Mettez en place un système de surveillance des conteneurs
4. Configurez un système de gestion des secrets pour les variables d'environnement sensibles 