import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
DB_DIR = os.path.join(BASE_DIR, "db")

def ingest_rules():
    print("Ingesting Rulebooks...")
    pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")]
    documents = []
    
    for pdf in pdf_files:
        path = os.path.join(DATA_DIR, pdf)
        print(f"Processing {pdf}...")
        loader = PyPDFLoader(path)
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = "rules"
            doc.metadata["filename"] = pdf
        documents.extend(docs)
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    
    vectorstore = Chroma(
        collection_name="rules",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=DB_DIR
    )
    vectorstore.add_documents(chunks)
    print(f"Added {len(chunks)} chunks to 'rules' collection.")

def ingest_adventure():
    print("Ingesting Adventure...")
    md_file = "Lost Mine of Phandelver.md"
    path = os.path.join(DATA_DIR, md_file)
    
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # Split by headers to keep context
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(text)
    
    # Further split large sections
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(md_header_splits)
    
    for chunk in chunks:
        chunk.metadata["source"] = "adventure"
        chunk.metadata["filename"] = md_file
        
    vectorstore = Chroma(
        collection_name="adventure",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=DB_DIR
    )
    vectorstore.add_documents(chunks)
    print(f"Added {len(chunks)} chunks to 'adventure' collection.")

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
    else:
        ingest_rules()
        ingest_adventure()
        print("Ingestion Complete!")
