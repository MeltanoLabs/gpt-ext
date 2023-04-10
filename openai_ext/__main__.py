"""OpenAI cli entrypoint."""
from openai_ext import extension

if __name__ == "__main__":
    extension.OpenAI.cli()
