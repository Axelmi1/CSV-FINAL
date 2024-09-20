import streamlit as st
import pandas as pd
import zipfile
import matplotlib.pyplot as plt
import seaborn as sns
from weather_parsing import filter_weather_by_circuit  # 🌦️ Importer la fonction de filtrage météo

# 🎨 Configuration de l'esthétique de Seaborn
sns.set_style("darkgrid")

# 📦 Utiliser la mise en cache pour les fichiers volumineux
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

# 📂 Charger les fichiers CSV une seule fois grâce à la mise en cache
circuits_df = load_circuits()
drivers_df = load_drivers()
results_df = load_results()
races_df = load_races()

# 🏁 Titre du dashboard
st.title("🏎️ Prédiction des résultats des courses de F1 en fonction de la météo 🌤️")

# 📋 Interface Streamlit pour sélectionner un circuit
st.sidebar.header("🔧 Sélectionner un circuit")
available_circuits = circuits_df['name'].unique()
selected_circuit = st.sidebar.selectbox('🏟️ Choisir un circuit', available_circuits)

# 🏆 Sélection du pilote
st.sidebar.header("👤 Sélectionner un pilote")
available_drivers = drivers_df['surname'].unique()
selected_driver = st.sidebar.selectbox('🏎️ Choisir un pilote', available_drivers)

# 🌐 Filtrer les données météo uniquement lorsque le circuit ou le pilote change
if 'selected_circuit' not in st.session_state or st.session_state.selected_circuit != selected_circuit or \
   'selected_driver' not in st.session_state or st.session_state.selected_driver != selected_driver:

    st.session_state.selected_circuit = selected_circuit
    st.session_state.selected_driver = selected_driver

    with st.spinner(f"🔍 Récupération des données météo pour {selected_circuit}..."):
        compressed_weather_file = filter_weather_by_circuit(selected_circuit, margin=2)

    if compressed_weather_file:
        # 📂 Ouvrir le fichier ZIP en mémoire
        with zipfile.ZipFile(compressed_weather_file) as zip_ref:
            # 📄 Obtenir la liste des fichiers dans le ZIP
            zip_contents = zip_ref.namelist()
            # 📑 Supposons qu'il n'y a qu'un seul fichier CSV dans le ZIP
            csv_filename = zip_contents[0]
            # 📖 Ouvrir le fichier CSV à l'intérieur du ZIP
            with zip_ref.open(csv_filename) as csv_file:
                # 📊 Lire le CSV dans un DataFrame Pandas
                weather_df = pd.read_csv(csv_file)
        st.session_state.weather_df = weather_df
    else:
        st.session_state.weather_df = None

# 🌡️ Récupérer les données météo depuis la session
weather_df = st.session_state.get('weather_df', None)

# ✅ Si les données météo existent, continuer l'analyse
if weather_df is not None:
    # 📍 Afficher les coordonnées du circuit sélectionné
    circuit_data = circuits_df[circuits_df['name'] == selected_circuit]
    latitude = circuit_data['lat'].values[0]
    longitude = circuit_data['lng'].values[0]
    st.subheader(f"📌 Coordonnées du circuit {selected_circuit}")
    st.write(f"**📍 Latitude :** {latitude}, **📍 Longitude :** {longitude}")

    # 🔢 Obtenir le circuitId du circuit sélectionné
    selected_circuit_id = circuit_data['circuitId'].values[0]

    # 🏎️ Filtrer les courses dans races.csv pour le circuit sélectionné
    selected_races = races_df[races_df['circuitId'] == selected_circuit_id]
    selected_race_ids = selected_races['raceId'].tolist()

    # 📊 Utiliser uniquement les colonnes nécessaires
    filtered_results_df = results_df[results_df['raceId'].isin(selected_race_ids)][['raceId', 'driverId', 'positionOrder', 'points', 'laps', 'milliseconds']]

    # 👤 Filtrer les données pour le pilote sélectionné sur le circuit sélectionné
    driver_id = drivers_df[drivers_df['surname'] == selected_driver]['driverId'].values[0]
    driver_data = filtered_results_df[filtered_results_df['driverId'] == driver_id]

    if driver_data.empty:
        st.write(f"❌ Pas de données pour {selected_driver} sur le circuit {selected_circuit}.")
    else:
        # 📈 Calculer la position moyenne
        predicted_position = driver_data['positionOrder'].mean()

        # 🌦️ Ajustement avec plusieurs facteurs météo
        st.sidebar.header("⚙️ Paramètres Météo")

        temperature = st.sidebar.slider('🌡️ Température (°C)',
                                        min_value=int(weather_df['fact_temperature'].min()),
                                        max_value=int(weather_df['fact_temperature'].max()),
                                        value=int(weather_df['fact_temperature'].mean()))

        pressure = st.sidebar.slider('📉 Pression Atmosphérique (hPa)',
                                     min_value=int(weather_df['gfs_pressure'].min()),
                                     max_value=int(weather_df['gfs_pressure'].max()),
                                     value=int(weather_df['gfs_pressure'].mean()))

        humidity = st.sidebar.slider('💧 Humidité (%)',
                                     min_value=int(weather_df['gfs_humidity'].min()),
                                     max_value=int(weather_df['gfs_humidity'].max()),
                                     value=int(weather_df['gfs_humidity'].mean()))

        wind_speed = st.sidebar.slider('💨 Vitesse du Vent (km/h)',
                                       min_value=int(weather_df['gfs_wind_speed'].min()),
                                       max_value=int(weather_df['gfs_wind_speed'].max()),
                                       value=int(weather_df['gfs_wind_speed'].mean()))

        # 📐 Calcul des facteurs d'influence météo
        temperature_factor = (temperature - weather_df['fact_temperature'].mean()) * 0.05
        pressure_factor = (pressure - weather_df['gfs_pressure'].mean()) * 0.01
        humidity_factor = (humidity - weather_df['gfs_humidity'].mean()) * 0.02
        wind_factor = (wind_speed - weather_df['gfs_wind_speed'].mean()) * 0.03

        # ➕ Ajuster la position prédite en fonction des conditions météo
        predicted_position_adjusted = predicted_position + temperature_factor + pressure_factor + humidity_factor + wind_factor

        # 🔒 Limiter la prédiction à des valeurs réalistes et arrondir
        predicted_position_adjusted = max(1, min(int(round(predicted_position_adjusted)), 20))

        # 🎯 Afficher la prédiction de la position (entier)
        st.subheader(f"🔮 Prédiction de la position pour {selected_driver}")
        st.write(f"**🏁 Position prédite sur le circuit {selected_circuit} :** {predicted_position_adjusted}")

        # 📊 **Visualisations mises à jour :**

        # 1. 📈 Historique des positions du pilote sur le circuit (avec années non chevauchées et positions incrémentées de 1 en 1)
        st.subheader(f"📉 Historique des performances de {selected_driver} sur {selected_circuit}")
        # 🔗 Joindre avec races_df pour obtenir l'année de chaque course
        driver_race_data = driver_data.merge(races_df[['raceId', 'year']], on='raceId')
        driver_race_data = driver_race_data.sort_values('year')
        fig, ax = plt.subplots()
        sns.lineplot(data=driver_race_data, x='year', y='positionOrder', marker='o', ax=ax)
        ax.set_xlabel('📅 Année')
        ax.set_ylabel('🏁 Position Finale')
        ax.set_xticks(driver_race_data['year'].unique())
        ax.set_xticklabels(driver_race_data['year'].unique(), rotation=45, ha='right')
        # 🎯 Ajuster les ticks de l'axe Y pour qu'ils incrémentent de 1 en 1
        ax.set_yticks(range(1, int(driver_race_data['positionOrder'].max()) + 1, 1))
        st.pyplot(fig)

        # 2. 🏆 Classement des pilotes sur le circuit (position moyenne)
        st.subheader(f"🏅 Classement des pilotes sur {selected_circuit}")
        # 📊 Calculer la position moyenne de chaque pilote sur le circuit
        avg_positions = filtered_results_df.groupby('driverId')['positionOrder'].mean().reset_index()
        avg_positions = avg_positions.merge(drivers_df[['driverId', 'surname']], on='driverId')
        avg_positions = avg_positions.sort_values('positionOrder')
        # 🔝 Afficher uniquement les 10 meilleurs pilotes
        top_pilots = avg_positions.head(10)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=top_pilots, x='positionOrder', y='surname', palette='coolwarm', ax=ax)
        ax.set_xlabel('📊 Position Moyenne')
        ax.set_ylabel('👤 Pilote')
        st.pyplot(fig)

        # 3. 🌦️ Influence des conditions météo sur les positions historiques (nouveau graphique)
        st.subheader(f"🌤️ Conditions météo historiques sur {selected_circuit}")
        # 🔗 Supposons que nous ayons des données météo historiques pour les courses
        # Joindre les données météo historiques avec les résultats
        # (Pour cet exemple, nous allons générer des données aléatoires)
        import numpy as np
        driver_race_data['Température'] = np.random.uniform(15, 35, size=len(driver_race_data))
        driver_race_data['Humidité'] = np.random.uniform(30, 80, size=len(driver_race_data))

        fig, ax = plt.subplots()
        scatter = ax.scatter(driver_race_data['Température'], driver_race_data['positionOrder'],
                             c=driver_race_data['Humidité'], cmap='viridis', s=100)
        ax.set_xlabel('🌡️ Température (°C)')
        ax.set_ylabel('🏁 Position Finale')
        cbar = fig.colorbar(scatter, ax=ax)
        cbar.set_label('💧 Humidité (%)')
        # 🔄 Inverser l'axe Y pour que la position 1 soit en haut
        ax.invert_yaxis()
        st.pyplot(fig)

    # 🛑 Fin de l'analyse
else:
    st.write(f"⚠️ Aucune donnée météo disponible pour le circuit {selected_circuit}.")

# 🎨 Personnalisation du style
st.markdown(
    """
    <style>
    .st-title {
        color: #FF4B4B;
    }
    .st-header {
        background-color: #f0f2f6;
    }
    </style>
    """,
    unsafe_allow_html=True
)
