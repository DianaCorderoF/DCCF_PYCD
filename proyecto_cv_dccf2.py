# -*- coding: utf-8 -*-
"""Proyecto CV_dccf.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1mBcsYJS1LE8nljqITXnnmq7CApH5R-MC
"""



import streamlit as st
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
import re
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity

import nltk
nltk.download('stopwords')

# Cargar el modelo de Hugging Face
@st.cache_resource  # Ideal para modelos como BERT
def load_model():
    tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
    model = AutoModel.from_pretrained('bert-base-uncased')
    return tokenizer, model
tokenizer, model = load_model()

# Función para cargar el dataset desde Google Drive (URL pública)
@st.cache_data # Cachear para mejorar rendimiento
def load_data(): 
    file_id = "110RlqRNEfZaB6zHr-CMDQgEoLi5MakukK"  
    url =  f"https://drive.google.com/uc?export=download&id={file_id}"
    return pd.read_csv(url)

df = load_data()
# Preprocesar el texto (eliminar stopwords, caracteres especiales, etc.)
stop_words = set(stopwords.words("english"))

def preprocess_text(text):
    # Convertir a minúsculas
    text = text.lower()

    # Eliminar caracteres especiales y números
    text = re.sub(r"[^a-zA-Z\s]", "", text)

    # Tokenizar y eliminar stopwords
    text_tokens = text.split()
    text_tokens = [word for word in text_tokens if word not in stop_words]

    # Reconstruir el texto preprocesado
    cleaned_text = " ".join(text_tokens)
    return cleaned_text

df['Processed_Resume'] = df['Resume'].apply(preprocess_text)


import ast  # Para convertir strings de embeddings en listas numéricas
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def recommend_similar_resumes(user_cv_embedding, df):
    similarities = []
    
    # Convertir la columna 'Embeddings' de string a listas
    df['Embeddings'] = df['Embeddings'].apply(lambda x: np.array(ast.literal_eval(x)))
    
    for _, row in df.iterrows():
        similarity = cosine_similarity(user_cv_embedding.reshape(1, -1), row['Embeddings'].reshape(1, -1))
        similarities.append(similarity[0][0])

    # Ordenar por similitud y devolver los 5 más similares
    df['Similarity'] = similarities
    recommended_resumes = df.sort_values(by='Similarity', ascending=False).head(5)
    
    return recommended_resumes


# Interfaz de usuario con Streamlit
st.title("Sistema de Recomendación de Empleos Basado en Currículums")

# Subir un archivo de CV
uploaded_file = st.file_uploader("Sube tu CV (txt o pdf)", type=["txt", "pdf"])

if uploaded_file is not None:
    # Preprocesar el CV
    if uploaded_file.type == "application/pdf":
        from pdfminer.high_level import extract_text
        cv_text = extract_text(uploaded_file)
    else:
        cv_text = uploaded_file.read().decode("utf-8")

    # Preprocesar el texto del CV
    processed_cv = preprocess_text(cv_text)

    # Obtener el embedding del CV subido por el usuario
    user_cv_embedding = get_embeddings(processed_cv)

    # Obtener recomendaciones basadas en la similitud con los currículums en el dataset
    recommendations = recommend_similar_resumes(user_cv_embedding, df)

    # Mostrar las recomendaciones
    st.write("Recomendaciones de Currículums Similares:")
    for _, row in recommendations.iterrows():
        st.write(f"**Categoría:** {row['Category']}")
        st.write(f"**Resumen del CV:** {row['Processed_Resume']}")
        st.write("---")