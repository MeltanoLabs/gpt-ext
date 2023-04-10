"""Create a ConversationalRetrievalChain for question/answering."""
import chromadb
from langchain.callbacks.base import AsyncCallbackManager
from langchain.callbacks.tracers import LangChainTracer
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.chat_vector_db.prompts import CONDENSE_QUESTION_PROMPT, QA_PROMPT
from langchain.chains.llm import LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.vectorstores import Chroma
from langchain.vectorstores.base import VectorStore


def load_chroma_vectorstore(chroma_dir) -> Chroma:
    """Load the Chroma vectorstore."""
    chroma = Chroma(
        embedding_function=OpenAIEmbeddings(model="text-embedding-ada-002"),
        client_settings=chromadb.config.Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=chroma_dir,
        ),
        collection_name="vector-db",
    )
    return chroma


def get_chain(
    vectorstore: VectorStore, question_handler, stream_handler, tracing: bool = False
) -> ConversationalRetrievalChain:
    """Create a ConversationalRetrievalChain for question/answering."""
    # Construct a ConversationalRetrievalChain with a streaming llm for combine docs
    # and a separate, non-streaming llm for question generation
    manager = AsyncCallbackManager([])
    question_manager = AsyncCallbackManager([question_handler])
    stream_manager = AsyncCallbackManager([stream_handler])
    if tracing:
        tracer = LangChainTracer()
        tracer.load_default_session()
        manager.add_handler(tracer)
        question_manager.add_handler(tracer)
        stream_manager.add_handler(tracer)

    question_gen_llm = OpenAI(
        temperature=0,
        verbose=True,
        callback_manager=question_manager,
    )
    streaming_llm = OpenAI(
        streaming=True,
        callback_manager=stream_manager,
        verbose=True,
        temperature=0,
    )

    question_generator = LLMChain(
        llm=question_gen_llm,
        prompt=CONDENSE_QUESTION_PROMPT,  # , callback_manager=manager
        verbose=True,
    )
    doc_chain = load_qa_chain(
        streaming_llm,
        chain_type="stuff",
        prompt=QA_PROMPT,  # , callback_manager=manager
        verbose=True,
    )
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=False)

    qa = ConversationalRetrievalChain(
        memory=memory,
        retriever=vectorstore.as_retriever(),
        combine_docs_chain=doc_chain,
        question_generator=question_generator,
        # callback_manager=manager,
    )
    # vectorstore=vectorstore,
    return qa
