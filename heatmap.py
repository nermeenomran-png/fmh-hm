import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np 
import plotly.express as px

#DataLoading
lives = pd.read_csv("notchcensus.csv")
providers = pd.read_csv("providers.csv")

#Clean
#ColumnNamesToLower
lives.columns = lives.columns.str.lower()
providers.columns = providers.columns.str.lower()

#DropNACoordinates
lives = lives.dropna(subset=['latitude', 'longitude'])
providers = providers.dropna(subset=['latitude', 'longitude'])
#consider grouping by lat and long and summing members to reduce number of points on the map, but for now we'll keep them as is for more granularity

#HaversineDistanceFunction
def haversine(lat1, lon1, lat2, lon2):
    R = 6371 

    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    return R * c

#CalculateNearestProvider
def find_nearest(lives_row, providers_df):
    distances = haversine(
        lives_row["latitude"],
        lives_row["longitude"],
        providers_df["latitude"],
        providers_df["longitude"]
    )
    idx = distances.idxmin()
    return pd.Series({
        "nearest_provider": providers_df.loc[idx, "name"],
        "distance_km": distances[idx]
    })

#UI
#Title  
st.title("Notch Census Coverage Heatmap")

#Sidebar
#Filters
practicearea_filter = st.sidebar.multiselect(
    "Filter by Practice Area", 
    options=providers["pa"].unique(), 
    default=providers["pa"].unique()
    )

#DistanceSlider
max_distance = st.sidebar.slider(
    "Max Distance to Provider (km)", 
    min_value=0, 
    max_value=500, 
    value=100
    )

#FilterProviders
filtered_providers = providers[providers["pa"].isin(practicearea_filter)]

#CalculateNearestProvider for filtered providers
lives[["nearest_provider", "distance_km"]] = lives.apply(lambda row: find_nearest(row, filtered_providers), axis=1)

#FilterData
filtered = lives[lives["distance_km"] <= max_distance]

#LivesHeatmap
fig = px.density_map(
    filtered,
    lat="latitude", 
    lon="longitude", 
    z="members", 
    radius=25,
    # consider dynamically adjusting radius center and zoom based on average of lat and long
    center=dict(lat=44.0, lon=-72.7),
    zoom=6,
    color_continuous_scale="Dense"
    )    

#ProviderPoints
provider_scatter = px.scatter_map(
    filtered_providers,
    lat="latitude",
    lon="longitude",
    hover_name="name",
    color="pa",
    color_discrete_sequence=px.colors.qualitative.Alphabet
)
fig.add_trace(
    provider_scatter.data[0]
)
st.plotly_chart(
    fig, 
    use_container_width=True
    )

#SummaryTable
st.subheader("Summary Table")
st.dataframe(
    filtered[[
        "state", 
        "nearest_provider", 
        "distance_km"
        ]].drop_duplicates().reset_index(drop=True)
)
"""
# Define heatmap layer
layer = pdk.Layer(
    "HeatmapLayer",
    data=df_tx,
    get_position='[longitude, latitude]',
    radiusPixels=50,
)

# Set map view (centered on Texas)
view_state = pdk.ViewState(
    latitude=31.0,
    longitude=-99.0,
    zoom=5,
)

# Render map
st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state
))
"""