#this script includes a lstm for preciditing hourly electricity consumption in munich for the year of 2024

import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import os
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout, BatchNormalization, TimeDistributed, RepeatVector
# from keras.preprocessing.sequence import TimeseriesGenerator
from sklearn.preprocessing import StandardScaler, MinMaxScaler, Normalizer, PowerTransformer
from keras.optimizers import Adam
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import requests
import time
from openmeter import OpenMeterClient
import matplotlib.pyplot as plt
from tensorflow.keras.initializers import HeNormal, GlorotUniform
from tensorflow.keras.regularizers import l2, l1, l1_l2
import seaborn as sns
from scipy.stats import boxcox
from bdew import get_load_profile_df
from tensorflow.keras.models import load_model
import tensorflow as tf

def get_lat_lon_from_plz(plz):
    """
    Get latitude and longitude from a German postal code (PLZ).

    Parameters:
        plz (str): The German postal code to search for.

    Returns:
        tuple: (latitude, longitude) as floats or (None, None) if not found.
    """
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': plz,  # Use the postal code as the query
        'countrycodes': 'de',  # Restrict search to Germany
        'format': 'json',
        'limit': 1,
        'addressdetails': 1
    }

    # Add a User-Agent header (replace with your actual email)
    headers = {
        'User-Agent': 'Bachelor_Thesis (ju.ebarbosa@gmail.com)'  # Replace with your email
    }

    try:
        response = requests.get(base_url, params=params, headers=headers)

        # Respect the rate limit of 1 request per second
        time.sleep(1)

        if response.status_code == 200:
            data = response.json()
            if data:
                lat = data[0]['lat']
                lon = data[0]['lon']
                return float(lat), float(lon)
            else:
                print(f"Could not find coordinates for PLZ {plz}")
                return None, None
        else:
            print(f"Error: {response.status_code}")
            return None, None
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None, None


# Function to get latitude and longitude for a given city name using Nominatim API
def get_lat_lon(city_name):
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': city_name,
        'format': 'json',
        'limit': 1,
        'addressdetails': 1
    }

    # Add a User-Agent header (replace 'your_email@example.com' with your actual email)
    headers = {
        'User-Agent': 'Bachelor_Thesis (ju.ebarbosa@gmail.com)'  # Replace with your email
    }

    response = requests.get(base_url, params=params, headers=headers)

    # Respect the rate limit of 1 request per second
    time.sleep(1)

    if response.status_code == 200:
        data = response.json()
        if data:
            lat = data[0]['lat']
            lon = data[0]['lon']
            return float(lat), float(lon)
        else:
            print(f"Could not find coordinates for {city_name}")
            return None, None
    else:
        print(f"Error: {response.status_code}")
        return None, None


def load_and_preprocess_om_data(directory_path):
    i = 0
    # Build a dataframe to append the relevant values for each sensor
    ppdata = pd.DataFrame(columns=['year', 'month', 'day', 'hour', 'latitude', 'longitude', 'area'])

    # fazer codigo pra ler os dados baixados no computador
    for filename in os.listdir(directory_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(directory_path, filename)
            data = pd.read_csv(file_path)

            # extract the city and area values from the first row
            for index, row in data.iterrows():  # Assuming you're looping through the data
                try:
                    # Extract the city and area values
                    plz = data[data.iloc[:, 0] == 'post_code'].iloc[:, 1].values[0]
                    area = data[data.iloc[:, 0] == 'area'].iloc[:, 1].values[0]


                except IndexError:
                    # Skip iteration if index is out of bounds
                    print(f"Skipping iteration at index {index} due to missing data in the file {filename}.")
                    continue

            # round area
            area = round(int(area), 0)

            # find city coordinates
            lat, lon = get_lat_lon_from_plz(plz)
            if lat is None or lon is None:
                continue
            lat, lon = round(lat, 3), round(lon, 3)

            # change the index of the first column to Zeitstempel
            old_column_name = data.columns[1]
            data = data.rename(columns={'id': 'Zeitstempel', old_column_name: 'Messwert'})

            # erase the first 21 rows containg inrelevant data and messing with the structure of the dataframe
            data = data[21:]

            # if column Zeitstempel exists then convert to datetime otherwise continue
            if 'Zeitstempel' not in data.columns:
                print('no Zeitstempel column')
                continue
            data['Zeitstempel'] = pd.to_datetime(data['Zeitstempel'], format='%Y-%m-%d %H:%M:%S')

            # Create columns for year, month, day, Hour
            data['year'] = data['Zeitstempel'].dt.year
            data['month'] = data['Zeitstempel'].dt.month
            data['day'] = data['Zeitstempel'].dt.day
            data['hour'] = data['Zeitstempel'].dt.hour

            # Check if the total number of rows matches 26280 (3 years of hourly data)
            if len(data) != 26280:
                # Define the date blocks to search for in the preferred order
                date_ranges = [
                    ((2021, 1, 1), (2023, 12, 31)), # Three years: 01.01.2021 - 31.12.2023
                    ((2021, 1, 1), (2022, 12, 31)),  # Two years: 01.01.2021 - 31.12.2022
                    ((2022, 1, 1), (2023, 12, 31)),  # Two years: 01.01.2022 - 31.12.2023
                    ((2023, 1, 1), (2023, 12, 31)),  # One year: 01.01.2023 - 31.12.2023
                    ((2022, 1, 1), (2022, 12, 31)),  # One year: 01.01.2022 - 31.12.2022
                    ((2021, 1, 1), (2021, 12, 31)),  # One year: 01.01.2021 - 31.12.2021
                ]

                # Iterate through the date ranges in the preferred order
                for start_date, end_date in date_ranges:
                    start_year, start_month, start_day = start_date
                    end_year, end_month, end_day = end_date

                    # Filter rows that fall within the current date range
                    mask = (
                                   (data['year'] > start_year) |
                                   ((data['year'] == start_year) & ((data['month'] > start_month) |
                                                                    ((data['month'] == start_month) & (
                                                                                data['day'] >= start_day))))
                           ) & (
                                   (data['year'] < end_year) |
                                   ((data['year'] == end_year) & ((data['month'] < end_month) |
                                                                  ((data['month'] == end_month) & (
                                                                              data['day'] <= end_day))))
                           )

                    # Get the filtered data
                    filtered_data = data[mask]

                    # Check if the block is valid (8760 rows for 1 year, 17520 rows for 2 years)
                    if len(filtered_data) == 8760 or len(filtered_data) == 17520 or len(filtered_data) == 26280:
                        # Assign the filtered block to the original data and exit
                        data = filtered_data
                        print(
                            f"Found a valid block of data from {start_year}-{start_month}-{start_day} to {end_year}-{end_month}-{end_day}.")
                        break
                else:
                    print("No valid block of data was found.")

            # erase column Zeitstempel
            data = data.drop(columns=['Zeitstempel'])

            # convert from str to float to perfom the operations
            data['Messwert'] = data['Messwert'].astype(float).round(2)

            # add columns for lat lon and area
            data['latitude'] = lat
            data['longitude'] = lon
            data['area'] = area

            # check if data has  rows, if not, next sensor
            # this is essencial for the LSTM later
            # check if len(data) is divisible by 365
            if len(data) % 8760 != 0:
                print('sensor with incomplete samples of size 8760')
                continue
            else:
                ppdata = pd.concat([ppdata, data], ignore_index=True)
                i += 1
                print(i)

    # save dataframe as a csv file so i dont have to run through all  buildings each time
    ppdata.to_csv(
        'C:/Users/jueba/PycharmProjects/bachelor_arbeit/bachelor_arbeit/open_smart_meter_data/hourly_munich/preprocessed_data_ANN.csv',
        index=False)

    return ppdata


def prepare_features(directory_path):
    # get a file from the directory_path
    file_path = os.path.join(directory_path, 'preprocessed_data_ANN.csv')
    data = pd.read_csv(file_path)


    # first convert area, lat, lon to float and date to numeric
    data['area'] = data['area'].astype(int)
    data['latitude'] = data['latitude'].astype(float).round(3)
    data['longitude'] = data['longitude'].astype(float).round(3)
    data['year'] = data['year'].astype(int)
    data['month'] = data['month'].astype(int)
    data['day'] = data['day'].astype(int)
    data['hour'] = data['hour'].astype(int)
    data['date'] = pd.to_datetime(data[['year', 'month', 'day', 'hour']])
    # Extract the day of the week (0 = Monday, 6 = Sunday)
    data['day_of_week'] = data['date'].dt.dayofweek

    print(data['Messwert'].describe())

    # Plot the  original distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(data["Messwert"], kde=True, bins=30, color='blue')
    plt.title("Distribution of Target Value 'Electricity Consumption'", fontsize=16)
    plt.xlabel("Electricity Consumption in kWh", fontsize=14)
    plt.ylabel("Frequency", fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()


    #identify rows with nan values
    nan_index = data[data['Messwert'].isna()].index
    # erase Nan values
    print(nan_index)
    data = data.dropna()


    #plot graphs
    data_plot = data.drop(columns=['year', 'month', 'day', 'hour', 'latitude', 'longitude', 'area'])
    data_plot = data_plot.set_index('date')
    data_plot = data_plot['Messwert']
    # plot every 8760 values in a new plot
    for i in range(0, 29):
        data_sample = data_plot[i * 8760:(i + 1) * 8760]

        #plt.plot(data_sample, label='Data', color='blue')



        #get the value area for this sensor
        title_area = data['area'][i * 8760]
        title_longitude = data['longitude'][i * 8760]
        title_year = data['year'][i * 8760]
        if title_area == 63:
            PLZ = '81549'
        elif title_area == 75:
            if title_longitude == 11.431:
                PLZ = '81245'
            else:
                PLZ = '81829'
        elif title_area == 78:
            PLZ = '81669'
        elif title_area == 98:
            PLZ = '81667'
        elif title_area == 110:
            PLZ = '81245'
        elif title_area == 115:
            PLZ = '80689'
        elif title_area == 120:
            PLZ = '80687'
        elif title_area == 151:
            PLZ = '80993'
        elif title_area == 180:
            PLZ = '81243'
        elif title_area == 200:
            PLZ = '81476'
        elif title_area == 300:
            PLZ = '81249'
        elif title_area == 462:
            PLZ = '81829'
        #plt.legend()
        #plt.title(f"Sample {(i+1)} with area {title_area} m2 and PLZ {PLZ}")
        #plt.xlabel('Time Step')
        #plt.ylabel('Energy Consumption (kWh)')
        # save plot as a png file
        #plt.savefig(f'C:/Users/jueba/Documents/BA/figures/plot_sample_area_{title_area}_{title_year}_{title_longitude}_original.png')
        #plt.show()

    # Normalize values
    scaler_year = MinMaxScaler()
    scaler_month = MinMaxScaler()
    scaler_day = MinMaxScaler()
    scaler_hour = MinMaxScaler()
    scaler_day_week = MinMaxScaler()
    scaler_y = MinMaxScaler()
    scaler_lat = MinMaxScaler()
    scaler_lon = MinMaxScaler()
    scaler_area = MinMaxScaler()

    year_scaled = scaler_year.fit_transform(data[['year']])
    month_scaled = scaler_month.fit_transform(data[['month']])
    day_scaled = scaler_day.fit_transform(data[['day']])
    hour_scaled = scaler_hour.fit_transform(data[['hour']])
    day_week_scaled = scaler_day_week.fit_transform(data[['day_of_week']])
    #create array target_area with lenght 254040 with areas between 20-400 filling with each area 8760 times
    # Define the range of areas
    areas = np.linspace(20, 500, num=254040 // 8760)  # Divide total length by repetition count
    # Repeat each area 8760 times to create the target_area array
    target_area = np.repeat(areas, 8760)
    scaler_area =  scaler_area.fit(target_area.reshape(-1, 1))
    area_scaled = scaler_area.transform(data[['area']])

    lat_scaled = scaler_lat.fit_transform(data[['latitude']])
    lon_scaled = scaler_lon.fit_transform(data[['longitude']])

    #creaet array target_y with lenght 254040 with random values between 0.0001 and 6.0000
    #target_y = np.random.uniform(0.0000, 6.0000, 254040)
    #scaler_y = scaler_y.fit(target_y.reshape(-1, 1))
    y_scaled = scaler_y.fit_transform(data[['Messwert']])

    # Combine all features (year, month, day, Hour, Area) into a single feature matrix
    X = np.concatenate([year_scaled, month_scaled, day_scaled, hour_scaled, day_week_scaled, area_scaled, lat_scaled, lon_scaled],
                       axis=1)
    y = y_scaled.flatten()  # Flatten y_scaled to be a 1D array for model compatibility

    return X, y, scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year


# Build the neural network
def build_model(X_train, y_train):
    print(X_train.shape[0], X_train.shape[1])

    model = Sequential()
    model.add(LSTM(64, activation="relu", return_sequences=True, input_shape=(24, 8)))
    model.add(LSTM(128, activation = "relu", return_sequences=True, input_shape=(24, 8),kernel_initializer=HeNormal(), kernel_regularizer=l2(0.01)))
    model.add(Dropout(0.3))
    model.add(LSTM(64, activation= "relu",return_sequences=True))
    model.add(Dropout(0.3))
    model.add(LSTM(32, activation= "relu",return_sequences=True))
    model.add(Dropout(0.3))
    model.add(TimeDistributed(Dense(1)))
    model.add(Dense(1))
    opt_adam = Adam(clipnorm=1.0, learning_rate=0.001)

    model.compile(opt_adam, loss='mean_squared_error', metrics=[tf.keras.metrics.RootMeanSquaredError(name='rmse')])

    model.summary()

    return model


# Load, preprocess, and train the model using multiple files
def train_energy_model(directory_path):

    # Load data from all files in the directory
    # all_data = load_and_preprocess_om_data(directory_path)

    # Prepare the features for model training
    X, y, scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year = prepare_features(directory_path)


    # the X has a length of 254040, equal to 29 yearly samples and to  daily samples with 24 hours each
    # split train test in 24 yearly samples for training which is a bit more than 80%
    #24*365*24 = 210240
    X_train = X[:210240]
    X_test = X[210240:]
    y_train = y[:210240]
    y_test = y[210240:]

    # Reshape the input data to be 3D for LSTM
    samples_train = int(X_train.shape[0] / 24)
    samples_test = int(X_test.shape[0] / 24)
    print('samples:', samples_train, samples_test)
    X_train = X_train.reshape(samples_train, 24, 8)
    X_test = X_test.reshape(samples_test, 24, 8)
    y_train = y_train.reshape(samples_train, 24)
    y_test = y_test.reshape(samples_test, 24)
    print("Shape of X_train:", X_train.shape)
    print("Shape of y_train:", y_train.shape)
    print("Shape of X_test:", X_test.shape)
    print("Shape of y_test:", y_test.shape)


    # Build and train the model
    '''model = build_model(X_train, y_train)

    # Store training history to plot loss
    history = model.fit(X_train, y_train, epochs=20, batch_size= 70080, validation_data=(X_test, y_test), verbose=1)



    mse, rmse = model.evaluate(X_test, y_test)
    print("these are the model results (loss:MSE, metrics: RMSE)", mse, rmse)


    print(history.history)

    # Plot the loss for each epoch
    plt.figure(figsize=(10, 6))
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss', linestyle='--')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training Loss Over Epochs')
    #plt.yscale('log')
    plt.legend()
    plt.show()'''

    #o melhro ate agora é o 70080 - melhor dmsple 27
    #o 3 eh pessimmo
    #o 4 sobe no verao ent tbm eh ruim

    model = load_model('./energy_consumption_final_model.keras')
    mse, rmse = model.evaluate(X_test, y_test)
    print("these are the model results (loss:MSE, metrics: RMSE)", mse, rmse)

    # Evaluate the model
    y_pred = model.predict(X_test)

    # make a table comparing the predicted values with the real values
    y_pred = scaler_y.inverse_transform(y_pred.reshape(-1, 1))
    y_test = scaler_y.inverse_transform(y_test.reshape(-1, 1))

    y_pred = y_pred.flatten()
    y_test = y_test.flatten()

    #clip all negative values from y_pred to zero
    y_pred = np.clip(y_pred, 0, None)


    #plot the real and predicted values for the test set
    entireslp_lstm = []
    entireslp_stats = []
    X_test_temp = X_test.reshape(-1, 8)

    #kundenwert based on the bdew statistical for average yearly electricity consumption
    #per household based on household size KW_stats_list = [1900, 2890, 3720, 4085, 5430]
    #the household areas of the samples were used to generate a number of residents
    #number of residents in household with 78m2 in samples 1 and 2: 1 residents >>>
    #number of residents in household with 98m2 in samples 3, 4 and 5: 2 residents >>>
    kw_stats = [1900,1900,2890,2890,2890]

    for i in range (0,5):
        #sum every 365 days of ytest
        kw = [sum(y_pred[i*8760: (i+1)*8760])]
        kw = int(kw[0])
        #get the year of this sample in x test

        year = X_test_temp[i*8760][0]
        year = scaler_year.inverse_transform([[year]])[0][0]
        year = int(year)

        area = X_test_temp[i*8760][5]
        area = scaler_area.inverse_transform([[area]])[0][0]
        area = int(area)
        print('area sample',i,'=',area)

        h0slp_lstm = get_load_profile_df.get_load_profile_df(year, kw)
        print('kw', kw)
        print('total bdew', h0slp_lstm['h0_dyn'].sum())
        h0slp_lstm = h0slp_lstm.resample('H').sum()
        print('total bdew after resampling', h0slp_lstm['h0_dyn'].sum())
        #add h0slp index to other two
        h0slp_lstm = h0slp_lstm.reset_index(drop=True)
        entireslp_lstm.append(h0slp_lstm['h0_dyn'])

        h0slp_stats = get_load_profile_df.get_load_profile_df(year, kw_stats[i])
        print('kw', kw_stats[i])
        print('total bdew', h0slp_stats['h0_dyn'].sum())
        h0slp_stats = h0slp_stats.resample('H').sum()
        print('total bdew after resampling', h0slp_stats['h0_dyn'].sum())
        # add h0slp index to other two
        h0slp_stats = h0slp_stats.reset_index(drop=True)
        entireslp_stats.append(h0slp_lstm['h0_dyn'])

        #plot 3 curves and y test in the same pop up
        plt.plot(y_test[i * 8760:(i + 1) * 8760], label='Real')  # Keep the real curve fully opaque
        plt.plot(h0slp_lstm, label='H0 SLP-Predicted with ELC_LSTM', alpha=0.7)  # Semi-transparent
        plt.plot(h0slp_stats, label='H0 SLP-Predicted with ELC_Stats', alpha=0.7)  # Semi-transparent
        plt.plot(y_pred[i * 8760:(i + 1) * 8760], label='LSTM-Predicted', alpha=0.7)  # Semi-transparent

        plt.legend()
        plt.title("Comparison of real consumption with the LSTM and BDEW\n"
                  f"generated curves for sample {(24 + i + 1)}")
        plt.xlabel('Time Step')
        plt.ylabel('Energy Consumption (kWh)')
        plt.savefig(f'C:/Users/jueba/Documents/BA/figures/plot_comparison_sample{24 + i}.png')
        plt.show()

        # plot ytest and ypred in the same pop up
        plt.plot(y_test[i * 8760:(i + 1) * 8760], label='Real')
        plt.plot(y_pred[i * 8760:(i + 1) * 8760], label='LSTM-Predicted')
        plt.legend()
        plt.title("Comparison of real consumption with the LSTM\n"
                  f"generated curves for sample {(24 + i + 1)}")
        plt.xlabel('Time Step')
        plt.ylabel('Energy Consumption (kWh)')
        plt.savefig(f'C:/Users/jueba/Documents/BA/figures/plot_comparison_sample{24 + i}_lstm.png')
        plt.show()

        # plot ytest and h0slp lstm in the same pop up
        plt.plot(y_test[i * 8760:(i + 1) * 8760], label='Real')
        plt.plot(h0slp_lstm, label='H0 SLP-Predicted with ELC_LSTM')
        plt.legend()
        plt.title("Comparison of real consumption with H0 SLP with ELC_LSTM\n"
                  f"generated curves for sample {(24 + i + 1)}")
        plt.xlabel('Time Step')
        plt.ylabel('Energy Consumption (kWh)')
        plt.savefig(f'C:/Users/jueba/Documents/BA/figures/plot_comparison_sample{24 + i}_h0slp_lstm.png')
        plt.show()

        # plot ytest and h0slp stats in the same pop up
        plt.plot(y_test[i * 8760:(i + 1) * 8760], label='Real')
        plt.plot(h0slp_stats, label='H0 SLP-Predicted with ELC_Stats')
        plt.legend()
        plt.title("Comparison of real consumption with H0 SLP with ELC_Stats\n"
                  f"generated curves for sample {(24 + i + 1)}")
        plt.xlabel('Time Step')
        plt.ylabel('Energy Consumption (kWh)')
        plt.savefig(f'C:/Users/jueba/Documents/BA/figures/plot_comparison_sample{24 + i}_h0slp_stats.png')
        plt.show()

        #plot onle the h0slp
        plt.plot(h0slp_lstm, label='H0 SLP-Predicted')
        plt.legend()
        plt.title(f"H0 SLP-Predicted for sample {(24+i+1)}")
        plt.xlabel('Time Step')
        plt.ylabel('Energy Consumption (kWh)')
        plt.show()

        #plot only the y pred
        plt.plot(y_pred[i*8760:(i+1)*8760], label='LSTM-Predicted')
        plt.legend()
        plt.title(f"LSTM-Predicted for sample {(24+i+1)}")
        plt.xlabel('Time Step')
        plt.ylabel('Energy Consumption (kWh)')
        plt.show()

        #plot the day 01.01 for each sample
        plt.plot(y_test[i * 8760: ((i * 8760)+24)], label='Real')  # Keep the real curve fully opaque
        plt.plot(h0slp_lstm[:24], label='H0 SLP-Predicted with ELC_LSTM', alpha=0.7)  # Semi-transparent
        plt.plot(h0slp_stats[:24], label='H0 SLP-Predicted with ELC_Stats', alpha=0.7)  # Semi-transparent
        plt.plot(y_pred[i * 8760: ((i * 8760)+24)], label='LSTM-Predicted', alpha=0.7)  # Semi-transparent
        plt.legend()
        plt.title("Comparison of real consumption with the LSTM and H0SLP\n")
        plt.title(f"Comparison of daily (01.01) consumption curves for sample {(24+i+1)}")
        plt.xlabel('Time Step')
        plt.ylabel('Energy Consumption (kWh)')
        plt.show()

    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    print(f"RMSE between y_test and y_pred: {rmse}")

    entireslp_lstm = np.array(entireslp_lstm).flatten()
    mae_bdew = mean_absolute_error(y_test, entireslp_lstm)
    rmse_bdew_lstm = mean_squared_error(y_test, entireslp_lstm, squared=False)
    print(f"RMSE between H0SLP_LSTM and y_test : {rmse_bdew_lstm}")

    entireslp_stats = np.array(entireslp_stats).flatten()
    mae_bdew = mean_absolute_error(y_test, entireslp_stats)
    rmse_bdew = mean_squared_error(y_test, entireslp_stats, squared=False)
    print(f"RMSE between H0SLP_LSTM and y_test : {rmse_bdew}")

    #calculate and print the max deviation for y pred, entireslp lstm, entireslp stats to y test
    max_deviation_y_pred = max(abs(y_test - y_pred))
    max_deviation_entireslp_lstm = max(abs(y_test - entireslp_lstm))
    max_deviation_entireslp_stats = max(abs(y_test - entireslp_stats))
    print(f"Max deviation between y_test and y_pred: {max_deviation_y_pred}")
    print(f"Max deviation between y_test and entireslp_lstm: {max_deviation_entireslp_lstm}")
    print(f"Max deviation between y_test and entireslp_stats: {max_deviation_entireslp_stats}")


    # Save the model and the scalers
    #model.save('C:/Users/jueba/PycharmProjects/bachelor_arbeit/bachelor_arbeit/energy_consumption_final_model_batch_70080_6.keras')

    return  scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year


# Define the function to estimate energy consumption for every hour of 2022
def estimate_energy_consumption( model, df, scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year):


    # Normalize year, month, day, hour
    year_scaled = scaler_year.transform(df[['year']])
    month_scaled = scaler_month.transform(df[['month']])
    day_scaled = scaler_day.transform(df[['day']])
    hour_scaled = scaler_hour.transform(df[['hour']])
    day_of_week_scaled = scaler_day_week.transform(df[['day_of_week']])

    # Normalize area
    df['area'] = df['area'].astype(int)
    area_scaled = scaler_area.transform(df[['area']])

    # Normalize latitude and longitude
    lat_scaled = scaler_lat.transform(df[['latitude']])
    lon_scaled = scaler_lon.transform(df[['longitude']])

    # Combine all features into a single feature matrix
    input_data = np.concatenate([year_scaled, month_scaled, day_scaled, hour_scaled, day_of_week_scaled, area_scaled, lat_scaled, lon_scaled], axis=1)
    # Ensure input_data has the right shape for LSTM
    input_data = input_data.reshape((1, 24, 8))

    # Predict yearly energy consumption
    estimated_consumption = model.predict(input_data)

    estimated_consumption = estimated_consumption.reshape(-1, 1)
    #estimated_consumption = estimated_consumption.flatten()

    # Inverse transform the predicted value to the original scale
    estimated_consumption = scaler_y.inverse_transform(estimated_consumption)


    # Return the array of energy consumption values
    return estimated_consumption


def predict_energy_consumption(model, h_area, lat, lon, scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year):
    # Create a dataframe for the input data
    df_input_pred = pd.DataFrame(columns=['year', 'month', 'day', 'hour', 'latitude', 'longitude', 'area'],
                                 index=range(0, 24))
    df = pd.DataFrame(columns=['date'])
    lat, lon = round(lat, 3), round(lon, 3)
    df_input_pred['latitude'] = lat
    df_input_pred['longitude'] = lon
    area = h_area
    df_input_pred['area'] = area

    # Initialize start date
    start_date = datetime.strptime("01.01.2024 00:00", "%d.%m.%Y %H:%M")

    # Determine if the year is a leap year
    year = start_date.year
    is_leap_year = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    # Number of days in the year
    days_in_year = 366 if is_leap_year else 365

    # Generate dataframes for each day
    #make lenght be 8760 lines
    all_days_dataframes = pd.DataFrame(columns=['Datetime', 'Energy Consumption (kWh)'])
    day_df = pd.DataFrame(columns=['Datetime', 'Energy Consumption (kWh)'])

    for day in range(days_in_year):
        # Create a list of hourly timestamps for the current day
        day_timestamps = [start_date + timedelta(hours=i) for i in range(0,24)]
        # Create a dataframe for the current day
        day_df = pd.DataFrame({"Datetime": day_timestamps})
        df_input_pred['year'] = day_df['Datetime'].dt.year
        df_input_pred['month'] = day_df['Datetime'].dt.month
        df_input_pred['day'] = day_df['Datetime'].dt.day
        df_input_pred['hour'] = day_df['Datetime'].dt.hour
        df_input_pred['day_of_week'] = day_df['Datetime'].dt.dayofweek
        estimated_consumption = estimate_energy_consumption(model, df_input_pred, scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year)

        #append in the first column of all_days_year the day_df and in th esecond column the estimated_consumption
        day_df['Energy Consumption (kWh)'] = estimated_consumption
        all_days_dataframes = pd.concat([all_days_dataframes, day_df], ignore_index=True)


        # Update start_date to the next day
        start_date += timedelta(days=1)


    print(all_days_dataframes)

    KW = sum(all_days_dataframes['Energy Consumption (kWh)'])
    return all_days_dataframes, KW





print(get_lat_lon_from_plz("80337"))

# Example usage:
directory_path = './open_smart_meter_data/hourly_munich'  # Replace with the actual path to your directory containing the 1000 files

#run the following code line if you want to preprocess the data yourself. For example in the case of another dataset. For the Open Meter DE datset for Munich
#this step is already done and does not need to be repeated, also because this step takes a while
#load_and_preprocess_om_data(directory_path)

# from openmeter.de  sensors are downloaded for the time 01.01.2021 - 01.01.2024
# i got 13 sensors with
#29 samples of 8760 measureements
#length 254040

# Train the model using all the files in the directory
#scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year= train_energy_model(directory_path)

#model = load_model('./energy_consumption_final_model.keras')

# Estimate energy consumption for a new household
#predict_energy_consumption(model,63, 48.125, 11.431, scaler_area, scaler_lat, scaler_lon, scaler_y, scaler_day, scaler_hour, scaler_day_week, scaler_month, scaler_year)
