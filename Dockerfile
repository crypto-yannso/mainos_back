FROM python:3.10-slim

WORKDIR /app

# Copier les fichiers de dépendances
COPY pyproject.toml setup.py .env.example ./

# Copier le contenu nécessaire
COPY README-MAINOS.md ./
COPY src/ ./src/

# Installation des dépendances
RUN pip install --no-cache-dir -e .

# Installer les dépendances optionnelles pour l'export
RUN pip install --no-cache-dir ".[export]"

# Exposer le port utilisé par l'application
EXPOSE 8080

# Configurer les variables d'environnement
ENV PYTHONPATH=/app

# Commande de démarrage
CMD ["python", "-m", "open_deep_research", "--host", "0.0.0.0", "--port", "8080"] 