import polars as pl
import pandas as pd
import joblib

# Charger les fichiers pilotes et standings
df_drivers = pl.read_csv('C:/Users/mazgo/Downloads/csv/drivers.csv')
df_driver_standings = pl.read_csv('C:/Users/mazgo/Downloads/csv/driver_standings.csv')

# Fonction pour sélectionner un pilote par son nom
def choisir_pilote(nom_pilote):
    # Filtrer le pilote choisi par son nom
    pilote = df_drivers.filter(pl.col('surname') == nom_pilote).to_pandas()
    if pilote.empty:
        print("Pilote non trouvé")
        return None
    return pilote.iloc[0]

# Exemple : Choisir un pilote
pilote_choisi = choisir_pilote('Verstappen')  # Remplace par le nom du pilote que tu veux

if pilote_choisi is not None:
    driver_id = pilote_choisi['driverId']
    
    # Obtenir l'historique du pilote à partir du driver_standings.csv
    pilote_historique = df_driver_standings.filter(pl.col('driverId') == driver_id)
    
    # Calculer des statistiques pour le pilote choisi
    total_wins = pilote_historique['wins'].sum()
    total_points = pilote_historique['points'].sum()
    average_position = pilote_historique['position'].mean()
    
    print(f"Pilote: {pilote_choisi['surname']}, Total Wins: {total_wins}, Total Points: {total_points}, Average Position: {average_position}")
    
    # Test avec différentes conditions météo
    weather_conditions = [
        {'climate_temperature': 30, 'gfs_wind_speed': 4.2, 'gfs_humidity': 80},   # Condition 1
        {'climate_temperature': 20, 'gfs_wind_speed': 20.2, 'gfs_humidity': 800},  # Condition 2
        {'climate_temperature': 40, 'gfs_wind_speed': 10.5, 'gfs_humidity': 60},   # Condition 3
        {'climate_temperature': 25, 'gfs_wind_speed': 5.0, 'gfs_humidity': 70},    # Condition 4
    ]
    
    # Charger le modèle de prédiction (RandomForest ou XGBoost)
    model = joblib.load('C:/Users/mazgo/Downloads/f1_prediction_model_with_pilot_history.pkl')  # ou avec XGBoost si tu as entraîné ce modèle
    
    # Tester différentes conditions météorologiques
    for i, weather in enumerate(weather_conditions):
        # Créer un DataFrame avec les conditions météo pour la prédiction
        X_new = pd.DataFrame([weather], columns=['climate_temperature', 'gfs_wind_speed', 'gfs_humidity'])

        # Ajouter la position de départ et l'historique du pilote pour la prédiction
        starting_position_pilote = 5  # Exemple de position de départ
        X_new['grid'] = starting_position_pilote
        X_new['total_wins'] = total_wins
        X_new['total_points'] = total_points
        X_new['average_position'] = average_position

        # Faire la prédiction avec le modèle chargé
        future_result = model.predict(X_new)
        print(f"Condition Météo {i + 1}: {weather}, Prédiction de la position finale: {future_result}")
