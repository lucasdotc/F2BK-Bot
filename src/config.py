from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

vector_store = Chroma(
    collection_name="F2BK_knowledge_base",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

