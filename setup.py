#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README-MAINOS.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mainos",
    version="0.1.0",
    author="Mainos Team",
    author_email="contact@mainos.ai",
    description="Plateforme intelligente de création de documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/votre-organisation/mainos",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Office/Business",
        "Topic :: Text Processing :: Markup",
    ],
    python_requires=">=3.10",
    install_requires=[
        "langchain>=0.1.0",
        "langchain-core>=0.1.0",
        "langgraph>=0.0.15",
        "langchain-community>=0.0.10",
        "langchain-openai>=0.0.2",
        "tavily-python>=0.2.7",
        "fastapi>=0.105.0",
        "uvicorn>=0.24.0",
        "pydantic>=2.5.2",
        "python-dotenv>=1.0.0",
        "jinja2>=3.1.2",
        "anthropic>=0.8.0",
        "sqlalchemy>=2.0.23",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "black>=23.11.0",
            "isort>=5.12.0",
            "mypy>=1.7.1",
        ],
        "export": [
            "weasyprint>=60.1",
            "python-pptx>=0.6.21",
            "python-docx>=1.0.1",
            "markdown>=3.5.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "mainos=open_deep_research.__main__:main",
        ],
    },
) 