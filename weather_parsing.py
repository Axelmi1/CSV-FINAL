import polars as pl
import pandas as pd
import os
import zipfile
import streamlit as st

# Utiliser la mise en cache pour éviter de refaire les mêmes calculs coûteux
@st.cache_data
def filter_weather_by_circuit(circuit_name, margin=10, max_size_mb=10):  # Ajuster la marge ici si nécessaire
    circuits_df = pd.read_csv('C:/Users/mazgo/Downloads/csv/circuits.csv')
    df_weather = pl.read_parquet('C:/Users/mazgo/Downloads/weather.parquet')

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

    # Sauvegarder les données météo filtrées dans un fichier CSV compressé
    if df_filtered_weather.shape[0] > 0:
        csv_file = f'C:/Users/mazgo/Downloads/{circuit_name}_weather.csv'
        df_filtered_weather.write_csv(csv_file)

        # Compresser le fichier CSV pour réduire la taille
        compressed_file = f'C:/Users/mazgo/Downloads/{circuit_name}_weather.zip'
        with zipfile.ZipFile(compressed_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(csv_file, arcname=f'{circuit_name}_weather.csv')

        return compressed_file
    else:
        return None
 