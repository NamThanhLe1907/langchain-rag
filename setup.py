from setuptools import setup, find_packages

setup(
    name="langchain_rag",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "langchain_core",
        "pydantic",
        "python-dotenv",
        "numpy",
        "requests",
        "pytz"
    ],
    extras_require={
        "dev": ["pytest", "flake8"]
    },
    entry_points={
        "console_scripts": [
            "langchain_rag=src.core.assistants.assistants:main"
        ],
    },
)