from setuptools import setup, find_packages

setup(
    name="ai-conversation-analyzer",
    version="2.0.0",
    author="Bryan Thompson",
    description="Advanced AI/ML system for semantic conversation analysis",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "colorama>=0.4.6",
        "chromadb>=0.4.15",
        "flask>=2.3.3",
        "redis>=4.6.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="ai ml conversation analysis semantic search vector database",
)