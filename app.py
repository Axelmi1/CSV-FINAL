import streamlit as st
import pandas as pd
import polars as pl
import gdown
import io
import zipfile
import os

# URL Google Drive du fichier Parquet
file_id = '18w_cf4LhZsb_I7TpyadAdMWcsyvrnRuo'
url = f'https://drive.google.com/uc?id={file_id}'

# Télécharger et charger les données météo depuis Google Drive
@st.cache_data
def load_weather_data():
    output = 'weather.parquet'
    
    # Vérifier si le fichier existe déjà pour éviter de télécharger plusieurs fois
    if not os.path.exists(output):
        # Télécharger le fichier à partir de Google Drive
        gdown.download(url, output, quiet=False)

    # Vérifier que le fichier a bien été téléchargé et est lisible
    if os.path.exists(output):
        try:
            return pl.read_parquet(output)
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier Parquet : {str(e)}")
            return None
    else:
        st.error("Le fichier weather.parquet n'a pas pu être téléchargé.")
        return None

# Charger les fichiers circuits et weather
@st.cache_data
def filter_weather_by_circuit(circuit_name, margin=10, max_size_mb=10):
    # Charger les fichiers circuits et weather
    circuits_df = pd.read_csv('circuits.csv')  # Chemin relatif vers le fichier CSV des circuits
    df_weather = load_weather_data()  # Appel à la fonction pour télécharger et charger le fichier Parquet

    # Si le fichier météo n'a pas pu être chargé, arrêter la fonction
    if df_weather is None:
        return None

    # Obtenir les coordonnées du circuit sélectionné
    circuit_data = circuits_df[circuits_df['name'] == circuit_name]
    if circuit_data.empty:
        return None
    
    latitude = circuit_data['lat'].values[0]
    longitude = circuit_data['lng'].values[0]

    # Filtrer les données météo pour ce circuit
    df_filtered_weather = df_weather.filter(
        (pl.col('fact_latitude').is_between(latitude - margin, latitude + margin)) &
        (pl.col('fact_longitude').is_between(longitude - margin, longitude + margin))
    )
    
    # Sélectionner seulement les colonnes pertinentes
    essential_columns = ['fact_latitude', 'fact_longitude', 'fact_temperature', 'gfs_pressure', 'gfs_humidity', 'gfs_wind_speed']
    df_filtered_weather = df_filtered_weather.select(essential_columns)

    # Échantillonner les données pour réduire le nombre de lignes (utiliser Polars sample method)
    sample_size = int(df_filtered_weather.shape[0] * 0.1)  # Prendre 10% des lignes
    df_filtered_weather = df_filtered_weather.sample(n=sample_size)

    # Sauvegarder les données météo filtrées dans un fichier CSV compressé en mémoire
    if df_filtered_weather.shape[0] > 0:
        # Sauvegarder le CSV dans un buffer en mémoire au lieu de l'écrire sur le disque
        csv_buffer = io.BytesIO()
        df_filtered_weather.write_csv(csv_buffer)
        csv_buffer.seek(0)  # Revenir au début du buffer

        # Créer un fichier zip dans un buffer en mémoire
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(f'{circuit_name}_weather.csv', csv_buffer.getvalue())
        
        zip_buffer.seek(0)  # Revenir au début du buffer

        # Retourner le buffer ZIP pour téléchargement
        return zip_buffer
    else:
        return None

# Initialiser la session state pour 'weather_df' si elle n'existe pas encore
if 'weather_df' not in st.session_state:
    st.session_state.weather_df = None

# Interface utilisateur Streamlit
st.title("Filtrer la météo par circuit")

# Entrée utilisateur pour le nom du circuit
circuit_name = st.text_input("Nom du circuit")

# Filtrer les données météo pour le circuit sélectionné
if circuit_name:
    if st.session_state.weather_df is None:
        with st.spinner(f"Fetching weather data for {circuit_name}..."):
            zip_file = filter_weather_by_circuit(circuit_name)
            if zip_file:
                st.session_state.weather_df = pd.read_csv(io.BytesIO(zip_file.read(zip_file.namelist()[0])))

    # Accéder aux données météo filtrées
    weather_df = st.session_state.weather_df

    # Si les données météo existent, continuer l'analyse
    if weather_df is not None:
        st.write("Données météo disponibles :")
        st.write(weather_df)
        
        # Proposer un bouton de téléchargement du fichier ZIP
        st.download_button(
            label="Télécharger les données météo compressées",
            data=zip_file,
            file_name=f'{circuit_name}_weather.zip',
            mime='application/zip'
        )
    else:
        st.write("Aucune donnée météo disponible pour ce circuit.")
