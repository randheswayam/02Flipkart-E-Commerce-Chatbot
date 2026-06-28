import pandas as pd 
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions 
import os
from groq import Groq
from dotenv import load_dotenv
from streamlit import context

load_dotenv()

# os.environ['GROQ_MODEL']


faqs_path = Path(__file__).parent / "resources/faq_data.csv"
chroma_client = chromadb.Client()
groq_client = Groq()
collection_name_faq = 'faqs'

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name='sentence-transformers/all-MiniLM-L6-v2'
    )


def ingest_faq_data(path):
    if collection_name_faq not in [c.name for c in chroma_client.list_collections()]:
        print("ingestion FAQ data into chromadb....")
        collection = chroma_client.get_or_create_collection(
            name=collection_name_faq,
            embedding_function=ef,

        )

        df = pd.read_csv(path)
        docs = df['question'].to_list()
        metadata = [{'answer': ans} for ans in df['answer'].to_list()]
        ids = [f"id_{i}" for i in range(len(docs))]

        collection.add(
            documents=docs,
            metadatas=metadata,
            ids=ids
        )
        print(f"FAQ Data successfully ingested into chroma collection: {collection_name_faq}")
    else:
        print(f"Collection {collection_name_faq} already exist!")

def get_relevent_qa(query):
    collection = chroma_client.get_or_create_collection(name=collection_name_faq)
    result = collection.query(
        query_texts=[query],
        n_results=2
    )
    return result


def faq_chain(query):
    result = get_relevent_qa(query)

    # context = ''.join([r.get('answer') for r in result['metadata'][0]])
    context = ''.join([r.get('answer') for r in result['metadatas'][0]])
    
    answer = generate_answer(query,context)

    return answer


def generate_answer(query,context):
    prompt = f''' Given the following context and question, generate answer based on this context only.
    If the answer is not found in the context, kindly state "I don't know". Don't try to make up an answer.


    QUESTION: {query}
   
    CONTEXT: {context}

    '''

    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=os.environ['GROQ_MODEL'],
    )

    # print(chat_completion.choices[0].message.content) 
    return chat_completion.choices[0].message.content
    



if __name__ == "__main__":
    ingest_faq_data(faqs_path)
    query = "whats's your policy on defective products?"
    # result = get_relevent_qa(query)
    # print(result)
    answer = faq_chain(query)
    print(answer)
