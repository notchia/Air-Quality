import os

os.chdir('..')
DATADIR = 'data'
SRCDIR = 'src'

import pandas as pd
import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt

DEFAULT_CRS = 'EPSG:3857'
SEASONS = ['summer', 'autumn']


# =============================================================================
# Formatting and cleaning functions
# =============================================================================
def lower_and_underscore(s):
    """Used to standardize column names"""
    return str(s).strip().lower().replace(' ','_')


# =============================================================================
# Data importing functions
# =============================================================================
def import_airnow_data():
    """Import AirNow data"""
    # Import summer and autumn AirNow data into a single DataFrame, adding 'season' column
    df_data = pd.DataFrame()
    for season in SEASONS:
        fname = os.path.join(DATADIR, f"{season}_2021_airnow.csv")
        df_tmp = pd.read_csv(fname, index_col=0, parse_dates=['DateTime'])
        df_tmp['season'] = season
        df_tmp.columns = df_tmp.columns.to_series().apply(lower_and_underscore)    
        df_data = df_data.append(df_tmp)
    
    # Get list of unique sensor coordinates and sort from southernmost to northermost
    df_sensor = df_data[['latitude', 'longitude']].drop_duplicates().sort_values(
        by='latitude').reset_index()
    df_sensor['coordinates'] = df_sensor.apply(lambda row: (row['latitude'], row['longitude']))
    locations = {{'coordinates': (41.670800, -87.732500), 'neighborhood': "Alsip", 'location': "W 122nd and S Orchard"},
                 {'coordinates': (41.754700, -87.713600), 'neighborhood': "Ashburn", 'location': "W 76th and S Lawndale"},
                 {'coordinates': (41.864329, -87.748826), 'neighborhood': "Cicero", 'location': "13th and S 49th (Liberty Elementary)"},
                 {'coordinates': (41.913600, -87.723900), 'neighborhood': "Humbolt Park/Hermosa", 'location': "W Bloomingdale and N Springfield"},
                 {'coordinates': (42.060300, -87.863100), 'neighborhood': "Des Plaines", 'location': "Harrison & Meadow (State Police)"}}          
    df_sensor = df_sensor.merge(pd.DataFrame(locations), on='coordinates', how='outer')
    
    return df_data, df_sensor

    '''
    df_an_pm25 = df_an_pm25.merge(sensorCoords_an[['latitude', 'longitude', 'location']],
                                  how='outer', on=['latitude', 'longitude'])
    '''

def import_purpleair_data():
    """Import PurpleAir data"""
    # Pull list of PurpleAir sensors from JSON file
    df_sensors = pd.read_json(os.path.join(DATADIR, "pa_sensors.json"))
    df_sensors.columns = df_sensors.columns.to_series().apply(lower_and_underscore)
    df_sensors.rename(columns={'sensorid': 'sensor'}, inplace=True)
    
    # Merge with coordinates for sensors locations (based on looking up intersections on Google Maps)
    sensorDict = {0: (41.82863695731357, -87.66789654012659),
                    1: (41.82492553658286, -87.67390925492755),
                    2: (41.82283856567223, -87.67588687024907)}
    
    df_sensors['coordinates'] = df_sensors.index.map(sensorDict)
    df_sensors['latitude'] = df_sensors['coordinates'].apply(lambda x: x[0])
    df_sensors['longitude'] = df_sensors['coordinates'].apply(lambda x: x[1])
    
    print(df_sensors[['sensor', 'neighborhood', 'location', 'latitude', 'longitude']])
    
    # Import summer and autumn PurpleAir parent (main sensor) data into a single DataFrame,
    # merging with sensor coordinates and adding 'season' column
    df_data = pd.DataFrame()
    for season in SEASONS:
        for source in ['parent', 'child']:
            fname = os.path.join(DATADIR, f"{season}_2021_pa_{source}.csv")
            df_tmp = pd.read_csv(fname, parse_dates=['created_at'])
            df_tmp['season'] = season
            df_tmp['source'] = source
            df_tmp.columns = df_tmp.columns.to_series().apply(lower_and_underscore)
            df_tmp.rename(columns={'created_at': 'datetime'}, inplace=True)
            df_tmp = df_tmp.merge(df_sensors[['sensor', 'latitude', 'longitude', 'location']], how='outer', on='sensor')
            df_data = df_data.append(df_tmp)
    
    return df_data, df_sensors
    
    '''
        # Get PM2.5-specific rows/cols
    # Get list of unique sensor coordinates
    colList = ['latitude', 'longitude', 'location', 'datetime', 'pm2.5_(cf=1)_ug/m3', 'season']
    df_pa_pm25 = df_data.sort_values(by=['latitude', 'datetime']).reset_index()
    df_pa_pm25.rename(columns={'pm2.5_(cf=1)_ug/m3': 'concentration'},  inplace=True)
    sensorCoords_pa = df_pa_pm25[['latitude', 'longitude', 'location']].drop_duplicates().sort_values(by='latitude').reset_index()
    '''

# =============================================================================
# Create and plot GeoDataFrames
# =============================================================================
def convert_to_gdf(df):
    gdf = gpd.GeoDataFrame(
        df,
        crs='EPSG:4326',
        geometry=gpd.points_from_xy(df.longitude, df.latitude), 
    ).to_crs(DEFAULT_CRS)
    return gdf


def plot_sensor_locations(saveflag=True):
    # Convert AirNow and PurpleAir sensor locations to GeoDataFrame
    gdf_an = convert_to_gdf(sensorCoords_an)
    gdf_pa = convert_to_gdf(sensorCoords_an)
    
    # Plot sensor locations: AirNow in red, PurpleAir in Blue
    ax = plt.figure((20,20))
    gdf_an.plot(ax=ax, color='red')
    gdf_pa.plot(ax=ax, color='blue')
    
    # Add background map
    ctx.add_basemap(ax)
    
    ax.set_axis_off()
    
    if saveFlag:
        plt.savefig('figures/sensor_locations_PM.png', bbox_inches='tight', dpi=600)