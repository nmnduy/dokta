from setuptools import setup, find_packages
setup(
    name="dokta",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai",
        "tiktoken",
        "sqlalchemy",
        "retrying",
    ],
    entry_points={
        "console_scripts": [
            "chat = dokta.chat:main"
        ]
    }
)
