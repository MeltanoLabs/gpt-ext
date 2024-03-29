"""Meltano GPT extension."""
from __future__ import annotations

import os
from typing import Any

import typer

from gpt_ext.ai import get_chain, load_chroma_vectorstore, load_pinecone_vectorstore
from gpt_ext.edk_fixes.extension_base import CLI, ExtensionBase

DEFAULT_SETTING_VALS = {
    "chroma_dir": os.path.join(os.path.expanduser("~"), ".chroma"),
}


class GPTExt(ExtensionBase):
    """Extension implementing the ExtensionBase interface."""

    supports_invoke_command = False
    supports_init_command = True

    def __init__(self) -> None:
        """Initialize the extension."""
        # self.openai_bin = "OpenAI"  # verify this is the correct name
        # self.openai_invoker = Invoker(self.openai_bin)
        self._vectorstore: Any | None = None

    @property
    def vectorstore(self) -> Any:
        if not self._vectorstore:
            if self.get_config("vectorstore") == "chroma":
                self.logger.info("Loading Chroma vectorstore.")
                _vectorstore = load_chroma_vectorstore(self.get_config("chroma_dir"))
            elif self.get_config("vectorstore") == "pinecone":
                self.logger.info("Loading Pinecone vectorstore.")
                _vectorstore = load_pinecone_vectorstore(
                    self.get_config("pinecone_api_key"),
                    self.get_config("pinecone_environment"),
                    self.get_config("pinecone_index"),
                    self.get_config("openai_api_key"),
                    self.get_config("pinecone_metadata_text_key"),
                )
        return _vectorstore

    def get_config(self, setting_name: str) -> Any:
        """Get a config setting."""
        env_var = setting_name.upper()
        if env_var in os.environ:
            return os.environ[env_var]
        env_var = "GPT_EXT_" + setting_name.upper()
        if env_var in os.environ:
            return os.environ[env_var]

        return DEFAULT_SETTING_VALS.get(setting_name, None)

    @CLI.command()
    @staticmethod
    def chat(
        ctx: typer.Context,
        question: str = typer.Option(..., prompt="What is your question?"),
    ) -> None:
        """Invoke the plugin.

        Note: that if a command argument is a list, such as command_args,
        then unknown options are also included in the list and NOT stored in the
        context as usual.
        """
        app: GPTExt = ctx.obj

        async def question_handler(text):
            print("Question:", text)
            result = typer.prompt("???")
            return result

        async def stream_handler(text):
            print("Stream:", text)

        qa = get_chain(
            app.vectorstore,
            question_handler=question_handler,
            stream_handler=stream_handler,
        )
        chat_history = []
        while True:
            result = qa({"question": question})
            print("---------------")
            print(f"Q: {result['question']}")
            print("---------------")
            print(result["answer"])
            print("---------------")
            print(chat_history)
            print("---------------")
            return  # Question history not working yet
            question = typer.prompt("Next question")
