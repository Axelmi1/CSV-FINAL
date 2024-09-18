import polars as pl
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
import matplotlib.pyplot as plt

# Charger les données combinées avec l'historique des pilotes
df_combined = pl.read_csv('C:/Users/mazgo/Downloads/singapore_combined_with_pilot_history.csv')

# Convertir la colonne 'position' en type numérique, en remplaçant les valeurs non numériques par NaN
df_combined = df_combined.with_columns(
    pl.col('position').cast(pl.Float64, strict=False).alias('position')
)

# Filtrer les lignes où 'position' est valide (i.e., non-null et non NaN)
df_combined = df_combined.filter(pl.col('position').is_not_null())

# Sélectionner les features supplémentaires incluant l'historique des pilotes
features = df_combined.select([
    'climate_temperature', 
    'gfs_wind_speed', 
    'gfs_humidity', 
    'grid',  # Position de départ
    'total_wins',  # Total des victoires du pilote
    'total_points',  # Points cumulés du pilote
    'average_position'  # Position moyenne du pilote
])

target = df_combined['position']  # Résultat final du pilote (cible)

# Convertir en DataFrame Pandas pour l'entraînement du modèle
X = features.to_pandas()
y = target.to_pandas()

# Diviser les données en ensemble d'entraînement et de test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entraîner le modèle RandomForest
model = RandomForestRegressor()
model.fit(X_train, y_train)

# Prédire les résultats sur l'ensemble de test
y_pred = model.predict(X_test)

# Calculer l'erreur quadratique moyenne
mse = mean_squared_error(y_test, y_pred)
print(f"RMSE (RandomForest): {mse ** 0.5}")

# *** Ajouter l'importance des features ***
importances = model.feature_importances_
feature_names = X.columns

# Afficher les features avec leur importance
for feature, importance in zip(feature_names, importances):
    print(f"{feature}: {importance}")

# Visualiser l'importance des features avec un graphique
plt.figure(figsize=(10, 6))
plt.barh(feature_names, importances)
plt.xlabel('Importance')
plt.ylabel('Features')
plt.title('Importance des Features dans le Modèle')
plt.show()

# Sauvegarder le modèle entraîné
joblib.dump(model, 'C:/Users/mazgo/Downloads/f1_prediction_model_with_pilot_history.pkl')
