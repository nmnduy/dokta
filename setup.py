from setuptools import setup, find_packages

setup(
    name="friday-chat",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai",
        # Add any other dependencies here
    ],
    entry_points={
        "console_scripts": [
            "chat = friday.chat:main"
        ]
    }
)
