from setuptools import find_packages, setup

setup(
    name="sonata-bot",
    version="0.1.0",
    package_dir={"": "bot"},
    packages=find_packages(where="bot"),
    py_modules=["bot"],
    entry_points={
        "console_scripts": [
            "sonata-bot = bot:main",
        ],
    },
    author="Educorreia932",
    description="A Discord bot for music lovers",
    python_requires=">=3.12",
)
