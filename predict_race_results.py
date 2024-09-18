import joblib
import pandas as pd

# Charger le modèle de prédiction
model = joblib.load('C:/Users/mazgo/Downloads/f1_prediction_model_with_pilot_history.pkl')

# Exemples de prévisions météo actuelles pour une course à Singapour
current_weather = {
    'climate_temperature': 30,  # Exemples de valeurs de température actuelle
    'gfs_wind_speed': 4.2,  # Exemples de valeurs de vitesse du vent
    'gfs_humidity': 80  # Exemples de valeurs d'humidité
}

# Créer un DataFrame avec les noms de colonnes (features) pour la prédiction
X_new = pd.DataFrame([current_weather], columns=['climate_temperature', 'gfs_wind_speed', 'gfs_humidity'])

# Ajouter la position de départ et l'historique du pilote pour la prédiction
starting_position_pilote = 15  # Par exemple, un pilote partant en 3ème position
total_wins = 5  # Total de victoires du pilote
total_points = 1500  # Total de points du pilote
average_position = 4  # Position moyenne du pilote

X_new['grid'] = starting_position_pilote
X_new['total_wins'] = total_wins
X_new['total_points'] = total_points
X_new['average_position'] = average_position

# Faire la prédiction avec le modèle chargé
future_result = model.predict(X_new)
print(f"Prédiction de la position finale du pilote : {future_result}")
