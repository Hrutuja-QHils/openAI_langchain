from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import CharacterTextSplitter
import os
import pinecone
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENV = os.getenv('PINECONE_ENV')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

def doc_preprocessing():
    loader = DirectoryLoader(
        'data/',
        glob='**/*.pdf',
        show_progress=True
    )
    docs = loader.load()
    text_splitter = CharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0
    )
    docs_split = text_splitter.split_documents(docs)
    return docs_split

@st.cache_resource
def embedding_db():
    embeddings = OpenAIEmbeddings()
    pinecone.Pinecone(
        api_key=PINECONE_API_KEY,
        environment=PINECONE_ENV
    )
    docs_split = doc_preprocessing()
    doc_db = Pinecone.from_documents(
        docs_split,
        embeddings,
        index_name='marathichatbot',
    )
    return doc_db

llm = ChatOpenAI()
doc_db = embedding_db()

def translate_to_marathi(text):
    translation_prompt = f"Translate the following English text to Marathi:\n\n{text}\n\nMarathi translation:"
    translation = llm.predict(translation_prompt)
    return translation

def retrieval_answer(query):
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type='stuff',
        retriever=doc_db.as_retriever(),
    )
    result = qa.run(query)
    marathi_result = translate_to_marathi(result)
    return marathi_result

def main():
    st.title("Marathi Chatbot")

    text_input = st.text_input("तुमचा प्रश्न विचारा...")

    if st.button("प्रश्न विचारा"):
        if len(text_input) > 0:
            st.info("तुमचा प्रश्न: " + text_input)
            answer = retrieval_answer(text_input)
            st.success(answer)

if __name__ == "__main__":
    main()