import polars as pl

# Charger les fichiers races et résultats
df_races = pl.read_csv('C:/Users/mazgo/Downloads/csv/races.csv')
df_results = pl.read_csv('C:/Users/mazgo/Downloads/csv/results.csv')

# Filtrer pour les courses ayant eu lieu à Singapour
df_singapore_race = df_races.filter(pl.col('name') == 'Singapore Grand Prix')

# Joindre les résultats des courses pour Singapour avec les informations des pilotes
df_singapore_results = df_results.join(df_singapore_race, on='raceId', how='inner')

# Afficher les premières lignes pour vérifier
print(df_singapore_results.head())

# Sauvegarder les résultats des courses pour Singapour
df_singapore_results.write_csv('C:/Users/mazgo/Downloads/singapore_race_results.csv')
