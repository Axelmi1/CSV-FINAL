import streamlit as st
import pandas as pd
from weather_parsing import filter_weather_by_circuit  # Importer la fonction de filtrage météo

# Utiliser la mise en cache pour les fichiers volumineux
@st.cache_data
def load_circuits():
    return pd.read_csv('circuits.csv')

@st.cache_data
def load_drivers():
    return pd.read_csv('drivers.csv')

@st.cache_data
def load_results():
    return pd.read_csv('results.csv')

@st.cache_data
def load_races():
    return pd.read_csv('races.csv')

# Charger les fichiers CSV une seule fois grâce à la mise en cache
circuits_df = load_circuits()
drivers_df = load_drivers()
results_df = load_results()
races_df = load_races()

# Utiliser circuits.csv pour lister les circuits disponibles dans la sélection
available_circuits = circuits_df['name'].unique()

# Interface Streamlit pour sélectionner un circuit
st.sidebar.header("Sélectionner un circuit")
selected_circuit = st.sidebar.selectbox('Choisir un circuit', available_circuits)

# Filtrer les données météo uniquement lorsque le circuit change
if 'selected_circuit' not in st.session_state or st.session_state.selected_circuit != selected_circuit:
    st.session_state.selected_circuit = selected_circuit
    with st.spinner(f"Fetching weather data for {selected_circuit}..."):
        compressed_weather_file = filter_weather_by_circuit(selected_circuit, margin=50)

    if compressed_weather_file:
        weather_df = pd.read_csv(compressed_weather_file.replace('.zip', '.csv'))  # Charger le fichier CSV extrait
        st.session_state.weather_df = weather_df
    else:
        st.session_state.weather_df = None

weather_df = st.session_state.weather_df

# Si les données météo existent, continuer l'analyse
if weather_df is not None:
    # Afficher les coordonnées du circuit sélectionné
    circuit_data = circuits_df[circuits_df['name'] == selected_circuit]
    latitude = circuit_data['lat'].values[0]
    longitude = circuit_data['lng'].values[0]
    st.write(f"Coordonnées du circuit {selected_circuit} :")
    st.write(f"Latitude: {latitude}, Longitude: {longitude}")

    # Obtenir les circuitId du circuit sélectionné
    selected_circuit_id = circuit_data['circuitId'].values[0]

    # Filtrer les courses dans races.csv pour le circuit sélectionné
    selected_race_ids = races_df[races_df['circuitId'] == selected_circuit_id]['raceId'].tolist()

    # Utiliser uniquement les colonnes nécessaires
    filtered_results_df = results_df[results_df['raceId'].isin(selected_race_ids)].filter(['raceId', 'driverId', 'positionOrder', 'points', 'laps', 'milliseconds'])

    # Sélection du pilote
    selected_driver = st.sidebar.selectbox('Choisir un pilote', drivers_df['surname'])

    # Filtrer les données pour le pilote sélectionné sur le circuit sélectionné
    driver_id = drivers_df[drivers_df['surname'] == selected_driver]['driverId'].values[0]
    driver_data = filtered_results_df[filtered_results_df['driverId'] == driver_id]

    if driver_data.empty:
        st.write(f"Pas de données pour {selected_driver} sur le circuit {selected_circuit}.")
    else:
        # Calculer la position moyenne
        predicted_position = driver_data['positionOrder'].mean()

        # Ajustement avec plusieurs facteurs météo
        st.sidebar.header("Paramètres Météo")
        
        temperature = st.sidebar.slider('Température (°C)', 
                                        min_value=int(weather_df['fact_temperature'].min()), 
                                        max_value=int(weather_df['fact_temperature'].max()), 
                                        value=int(weather_df['fact_temperature'].mean()))

        pressure = st.sidebar.slider('Pression Atmosphérique (hPa)', 
                                     min_value=int(weather_df['gfs_pressure'].min()), 
                                     max_value=int(weather_df['gfs_pressure'].max()), 
                                     value=int(weather_df['gfs_pressure'].mean()))

        humidity = st.sidebar.slider('Humidité (%)', 
                                     min_value=int(weather_df['gfs_humidity'].min()), 
                                     max_value=int(weather_df['gfs_humidity'].max()), 
                                     value=int(weather_df['gfs_humidity'].mean()))

        wind_speed = st.sidebar.slider('Vitesse du Vent (km/h)', 
                                       min_value=int(weather_df['gfs_wind_speed'].min()), 
                                       max_value=int(weather_df['gfs_wind_speed'].max()), 
                                       value=int(weather_df['gfs_wind_speed'].mean()))

        # Calcul des facteurs d'influence météo
        temperature_factor = (temperature - weather_df['fact_temperature'].mean()) * 0.05
        pressure_factor = (pressure - weather_df['gfs_pressure'].mean()) * 0.01
        humidity_factor = (humidity - weather_df['gfs_humidity'].mean()) * 0.02
        wind_factor = (wind_speed - weather_df['gfs_wind_speed'].mean()) * 0.03

        # Ajuster la position prédite en fonction des conditions météo
        predicted_position_adjusted = predicted_position + temperature_factor + pressure_factor + humidity_factor + wind_factor

        # Limiter la prédiction à des valeurs réalistes et arrondir
        predicted_position_adjusted = max(1, min(int(round(predicted_position_adjusted)), 20))

        # Afficher la prédiction de la position (entier)
        st.write(f"**Prédiction de la position pour {selected_driver} sur le circuit {selected_circuit} :** {predicted_position_adjusted}")


else:
    st.write(f"Aucune donnée météo disponible pour le circuit {selected_circuit}.")
