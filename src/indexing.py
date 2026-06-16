import os
import glob as glob_module
import logging
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config import vector_store


def run_indexing(knowledge_dir="knowledge"):
    md_files = glob_module.glob(f"{knowledge_dir}/**/*.md", recursive=True)

    if not md_files:
        logging.info("No .md files found in knowledge/ — skipping indexing.")
        return

    # Find which sources are already in the vector store
    existing = vector_store.get(include=["metadatas"])
    indexed_sources = {os.path.normpath(m.get("source", "")) for m in existing["metadatas"]}

    new_files = [f for f in md_files if os.path.normpath(f) not in indexed_sources]

    if not new_files:
        logging.info(f"All {len(md_files)} file(s) already indexed — skipping.")
        return

    logging.info(f"Indexing {len(new_files)} new file(s): {new_files}")

    docs = []
    for filepath in new_files:
        loader = TextLoader(filepath, encoding="utf-8")
        docs.extend(loader.load())

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, add_start_index=True)
    chunks = text_splitter.split_documents(docs)

    logging.info(f"Split into {len(chunks)} chunks.")
    vector_store.add_documents(documents=chunks)
    logging.info("Indexing complete.")
