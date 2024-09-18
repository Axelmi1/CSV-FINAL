import polars as pl
import pandas as pd
from datetime import datetime, timezone

# Charger les fichiers météo et résultats des courses de Singapour
df_singapore_weather = pl.read_csv('C:/Users/mazgo/Downloads/csv/singapore_weather.csv')
df_singapore_results = pl.read_csv('C:/Users/mazgo/Downloads/csv/singapore_race_results.csv')

# Convertir le DataFrame Polars en Pandas pour transformer le timestamp
df_singapore_weather_pandas = df_singapore_weather.to_pandas()

# Convertir le timestamp en format 'YYYY-MM-DD' dans Pandas
df_singapore_weather_pandas['date'] = df_singapore_weather_pandas['fact_time'].apply(
    lambda x: datetime.fromtimestamp(x, timezone.utc).strftime('%Y-%m-%d')
)

# Revenir à Polars après la transformation
df_singapore_weather = pl.from_pandas(df_singapore_weather_pandas)

# Supprimer la colonne 'fact_time' (ancien timestamp) car elle n'est plus nécessaire
df_singapore_weather = df_singapore_weather.drop('fact_time')

# Filtrer uniquement les résultats de la course principale à Singapour (toutes les années)
df_singapore_results_filtered = df_singapore_results.filter(
    (pl.col('positionOrder').is_not_null())  # Filtrer uniquement les résultats de la course principale
)

# Joindre les données météo avec les résultats de la course de Singapour sur la colonne "date"
df_combined = df_singapore_results_filtered.join(df_singapore_weather, how='inner', on=['date'])

# Vérifier les doublons après la jointure
if df_combined.is_duplicated().sum() > 0:
    print(f"Nombre de doublons avant suppression : {df_combined.is_duplicated().sum()}")
    # Supprimer les doublons
    df_combined = df_combined.unique()

# Afficher les premières lignes pour vérifier la jointure
print(df_combined.head())

# Sauvegarder les données combinées
df_combined.write_csv('C:/Users/mazgo/Downloads/singapore_combined_data_all_years.csv')
