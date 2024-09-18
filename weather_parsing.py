import polars as pl
import pandas as pd
import io
import zipfile
import streamlit as st

# Utiliser la mise en cache pour éviter de refaire les mêmes calculs coûteux
@st.cache_data
def filter_weather_by_circuit(circuit_name, margin=10, max_size_mb=10):
    # Charger les fichiers circuits et weather
    circuits_df = pd.read_csv('circuits.csv')  # Chemin relatif vers le fichier CSV des circuits
    df_weather = pl.read_parquet('weather.parquet')  # Chemin relatif vers le fichier Parquet des données météo

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

# Interface utilisateur Streamlit
st.title("Filtrer la météo par circuit")

# Entrée utilisateur pour le nom du circuit
circuit_name = st.text_input("Nom du circuit")

if circuit_name:
    # Filtrer les données météo pour le circuit sélectionné
    zip_file = filter_weather_by_circuit(circuit_name)
    
    if zip_file:
        # Proposer un bouton de téléchargement du fichier ZIP
        st.download_button(
            label="Télécharger les données météo compressées",
            data=zip_file,
            file_name=f'{circuit_name}_weather.zip',
            mime='application/zip'
        )
    else:
        st.write("Aucune donnée météo disponible pour ce circuit.")
