from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="anything-to-llms-txt",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Universal document converter to structured LLMs.txt format",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/anything-to-llms-txt",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "llmstxt=src.main:main",
        ],
    },
)
