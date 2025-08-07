#!/usr/bin/env python3
"""
Local Multi-Agent Collaborative System Setup

A comprehensive multi-agent collaboration system using Ollama for LLM inference.
Implements a 4-phase workflow: Analysis → Critique → Synthesis → Consensus.
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Local Multi-Agent Collaborative System using Ollama for LLM inference"

# Read requirements from requirements.txt
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements

# Read test requirements
def read_test_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'tests', 'test_requirements.txt')
    requirements = []
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements

setup(
    name="local-agent-system",
    version="1.0.0",
    author="Local Agent System Team",
    author_email="contact@localagentsystem.dev",
    description="Multi-agent collaboration system using Ollama for LLM inference",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/local-agent-system",
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    package_data={
        'local_agent_system': [
            'config/presets/*.yaml',
            'config/*.yaml',
            'prompts/*.txt',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        'dev': read_test_requirements() + [
            'black>=23.0.0',
            'isort>=5.12.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
            'bandit>=1.7.0',
            'safety>=2.3.0',
        ],
        'test': read_test_requirements(),
        'performance': [
            'memory_profiler>=0.60.0',
            'psutil>=5.9.0',
            'matplotlib>=3.6.0',  # For benchmark visualization
        ],
        'enhanced': [
            'rich>=13.7.0',       # Enhanced terminal output
            'colorama>=0.4.6',    # Cross-platform colored output  
            'orjson>=3.8.0',      # Faster JSON processing
        ]
    },
    entry_points={
        'console_scripts': [
            'local-agent-system=main:main',
            'agent-system=main:main',
            'run-agent-tests=tests.run_tests:main',
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/local-agent-system/issues",
        "Source": "https://github.com/yourusername/local-agent-system",
        "Documentation": "https://github.com/yourusername/local-agent-system/wiki",
        "Changelog": "https://github.com/yourusername/local-agent-system/blob/main/CHANGELOG.md",
    },
    keywords=[
        "ai", "agents", "multi-agent", "collaboration", "llm", "ollama", 
        "artificial-intelligence", "natural-language-processing", "distributed-systems"
    ],
    zip_safe=False,
)
