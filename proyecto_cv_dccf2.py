# -*- coding: utf-8 -*-
"""Proyecto CV_dccf.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1mBcsYJS1LE8nljqITXnnmq7CApH5R-MC
"""



import streamlit as st
import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
import re
import gdown
from pdfminer.high_level import extract_text
import ast  # Para convertir strings de embeddings en listas numéricas
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')

# Cargar el modelo de Hugging Face
@st.cache_resource  # Ideal para modelos como BERT
def load_model():
    tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
    model = AutoModel.from_pretrained('bert-base-uncased')
    return tokenizer, model
tokenizer, model = load_model()

# Función para cargar el dataset desde Google Drive (URL pública)

@st.cache_data
def load_data():
    file_id = "10RlqRNEfZaB6zHr-CMDQgEoLi5MakukK"
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    output = "dataset.csv"
    gdown.download(url, output, quiet=False)
    return pd.read_csv(output)

df = load_data()
# Preprocesar el texto (eliminar stopwords, caracteres especiales, etc.)
stop_words = set(stopwords.words("english"))

def preprocess_text(text):
    if not isinstance(text, str):  # Evitar errores con valores NaN
        return ""
    
    text = text.lower()
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    
    text_tokens = text.split()
    text_tokens = [word for word in text_tokens if word not in stop_words]
    
    return " ".join(text_tokens)

df['Processed_Resume'] = df['Resume'].fillna("").apply(preprocess_text)


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
    try:
        # Extraer texto del CV
        if uploaded_file.type == "application/pdf":
            cv_text = extract_text(uploaded_file)
        else:
            cv_text = uploaded_file.read().decode("utf-8")

        if not cv_text.strip():  # Verificar si el archivo está vacío
            st.error("El archivo subido está vacío. Por favor, sube un CV válido.")
        else:
            processed_cv = preprocess_text(cv_text)

            # Buscar el embedding más similar en el dataset
            user_cv_embedding = np.mean(np.stack(df['Embeddings'].values), axis=0)  # Aproximación si no tienes un embedding real

            # Obtener recomendaciones
            recommendations = recommend_similar_resumes(user_cv_embedding, df)

            # Mostrar resultados
            st.write("### Recomendaciones de Currículums Similares:")
            for _, row in recommendations.iterrows():
                st.write(f"**Categoría:** {row['Category']}")
                st.write(f"**Resumen del CV:** {row['Processed_Resume']}")
                st.write("---")
    except Exception as e:
    st.error(f"Ocurrió un error al procesar el archivo: {e}")