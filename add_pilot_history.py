import polars as pl

# Charger les fichiers combinés, pilotes, et standings
df_combined = pl.read_csv('C:/Users/mazgo/Downloads/singapore_combined_data_all_years.csv')
df_drivers = pl.read_csv('C:/Users/mazgo/Downloads/csv/drivers.csv')
df_driver_standings = pl.read_csv('C:/Users/mazgo/Downloads/csv/driver_standings.csv')

# Calculer le nombre total de victoires pour chaque pilote
df_victories = df_driver_standings.group_by('driverId').agg(
    pl.col('wins').sum().alias('total_wins')
)

# Joindre les victoires avec les informations des pilotes dans les données combinées
df_combined = df_combined.join(df_victories, on='driverId', how='left')

# Ajouter d'autres statistiques comme podiums et positions moyennes
df_podiums = df_driver_standings.group_by('driverId').agg(
    pl.col('points').sum().alias('total_points'),
    pl.col('position').mean().alias('average_position')
)

df_combined = df_combined.join(df_podiums, on='driverId', how='left')

# Sauvegarder les données combinées avec l'historique des pilotes
df_combined.write_csv('C:/Users/mazgo/Downloads/singapore_combined_with_pilot_history.csv')

# Vérification des premières lignes
print(df_combined.head())
