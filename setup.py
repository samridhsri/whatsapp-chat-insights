from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="whatsapp-chat-analyzer",
    version="1.0.0",
    author="WhatsApp Chat Analyzer Team",
    description="A production-grade WhatsApp chat analysis tool with Streamlit UI and CLI support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/whatsapp-chat-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Chat",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "full": [
            "wordcloud>=1.9.0",
            "matplotlib>=3.7.0",
            "pillow>=10.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "whatsapp-analyzer=whatsapp_analyzer.cli:main",
        ],
    },
) 