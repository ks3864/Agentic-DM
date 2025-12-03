from pypdf import PdfReader
import os

def read_pdf_head(path, pages=3):
    try:
        reader = PdfReader(path)
        text = ""
        for i in range(min(pages, len(reader.pages))):
            text += reader.pages[i].extract_text() + "\n---\n"
        return text
    except Exception as e:
        return f"Error reading {path}: {e}"

data_dir = "d:/COMS6998_LLM_GenAI/agenticdm/data"
files = [f for f in os.listdir(data_dir) if f.endswith(".pdf")]

for f in files:
    print(f"--- Reading {f} ---")
    print(read_pdf_head(os.path.join(data_dir, f)))
    print("\n=================\n")
