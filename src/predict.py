########### Libraries ###########
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from flask import Flask
from xgboost import XGBRegressor
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")
############################## Preprocess Function ##############################
def preprocess(node10fish, node22fish, node10temp, node22temp):
    ########### Drop Unnecessary Columns ###########
    columns_fish = ['LOCAL_DATE', 'TOTAL', 'PEAK_TIME']
    node10fish = node10fish[columns_fish]
    node22fish = node22fish[columns_fish]

    columns_temp = ['LOCAL_DATE', 'MEAN_TEMPERATURE', 'MEAN_TEMPERATURE_YESTERDAY', 'TOTAL_PRECIPITATION', 'TOTAL_PRECIPITATION_YESTERDAY']
    node10temp = node10temp[columns_temp]
    node22temp = node22temp[columns_temp]

    ########### Impute ###########
    node10fish.replace('?', np.nan, inplace=True)
    node22fish.replace('?', np.nan, inplace=True)
    node10temp.replace('?', np.nan, inplace=True)
    node22temp.replace('?', np.nan, inplace=True)

    imputer = SimpleImputer(strategy='median') #Median
    node10fish[node10fish.columns.difference(['LOCAL_DATE'])] = imputer.fit_transform(node10fish[node10fish.columns.difference(['LOCAL_DATE'])])
    node22fish[node22fish.columns.difference(['LOCAL_DATE'])] = imputer.fit_transform(node22fish[node22fish.columns.difference(['LOCAL_DATE'])])

    node10temp[node10temp.columns.difference(['LOCAL_DATE'])] = imputer.fit_transform(node10temp[node10temp.columns.difference(['LOCAL_DATE'])])
    node22temp[node22temp.columns.difference(['LOCAL_DATE'])] = imputer.fit_transform(node22temp[node22temp.columns.difference(['LOCAL_DATE'])])


    ########### Remove Noise ###########
    window_size = 9 #CMA Window Size
    node10fish['PEAK_TIME'] = node10fish['PEAK_TIME'].rolling(window=window_size, center=True).mean()
    node10fish['TOTAL'] = node10fish['TOTAL'].rolling(window=window_size, center=True).mean()

    node22fish['PEAK_TIME'] = node22fish['PEAK_TIME'].rolling(window=window_size, center=True).mean()
    node22fish['TOTAL'] = node22fish['TOTAL'].rolling(window=window_size, center=True).mean()


    ########### Join with temp on date column ###########
    node10 = pd.merge(node10fish, node10temp, on='LOCAL_DATE', how='inner')
    node22 = pd.merge(node22fish, node22temp, on='LOCAL_DATE', how='inner')


    ########### Drop Unnecessary Columns ###########
    node10 = node10[node10.columns.difference(['LOCAL_DATE'])]
    node22 = node22[node22.columns.difference(['LOCAL_DATE'])]
    
    ########### Drop Unnecessary Rows ###########
    node10 = node10.dropna(subset=['TOTAL'])
    node22 = node22.dropna(subset=['TOTAL'])
    
    ########### Return Values ###########
    return node10, node22




############################## Linear Regression ##############################
'''
def linear_regression(node, target):
    features = ['MEAN_TEMPERATURE', 'MEAN_TEMPERATURE_YESTERDAY', 'TOTAL_PRECIPITATION', 'TOTAL_PRECIPITATION_YESTERDAY']

    X_node = node[features]
    y_node = node[target]
    
    model = LinearRegression()

    ########### Train model ###########
    model.fit(X_node, y_node)

    ########### Return Trained model ###########
    return model
'''




############################## XGB Regressor ##############################
def xgb_regression(node, target):
    features = ['MEAN_TEMPERATURE', 'MEAN_TEMPERATURE_YESTERDAY', 'TOTAL_PRECIPITATION', 'TOTAL_PRECIPITATION_YESTERDAY']

    X = node[features]
    y = node[target]

    # Standardize the Data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Build XGBRegressor Model
    model = XGBRegressor(objective='reg:squarederror', random_state=42)

    # Train XGBRegressor Model
    model.fit(X_scaled, y)

    return model




############################## convert_min_to_time ##############################
def convert_min_to_time(minutes):
    # Calculate hours and minutes
    hours = minutes // 60
    minutes %= 60

    # Format as hh:mm
    formatted_time = '{:02d}:{:02d}'.format(int(hours), int(minutes))
    return formatted_time

    
    

############################## Main ##############################
########### Data ###########
node10fish = pd.read_csv("src/Datasets/Node10.csv")
node22fish = pd.read_csv("src/Datasets/Node22.csv")
node10temp = pd.read_csv("src/Datasets/TempNode10.csv")
node22temp = pd.read_csv("src/Datasets/TempNode22.csv")


########### Preprocess ###########
node10, node22 = preprocess(node10fish, node22fish, node10temp, node22temp)


########### Model Generation ###########
linear_regression_time_model = LinearRegression()
linear_regression_total_model = LinearRegression()
    

########### Predict ###########
@socketio.on('predict')
def handle_prediction(data):
    node = data['node']
    today_temp = float(data['todayTemp'])
    today_precip = float(data['todayPrecip'])
    yesterday_temp = float(data['yesterdayTemp'])
    yesterday_precip = float(data['yesterdayPrecip'])
    
    if node == 'Node10':
        linear_regression_time_model = xgb_regression(node10, 'PEAK_TIME')
        linear_regression_total_model = xgb_regression(node10, 'TOTAL')
        input_data = np.array([[today_temp, yesterday_temp, today_precip, yesterday_precip]])
        prediction_time = convert_min_to_time(linear_regression_time_model.predict(input_data))
        prediction_total = linear_regression_total_model.predict(input_data)
        emit('prediction_result', {'time': str(prediction_time), 'total': int(prediction_total[0])})
        
    else:
        linear_regression_time_model = xgb_regression(node22, 'PEAK_TIME')
        linear_regression_total_model = xgb_regression(node22, 'TOTAL')
        input_data = np.array([[today_temp, yesterday_temp, today_precip, yesterday_precip]])
        prediction_time = convert_min_to_time(linear_regression_time_model.predict(input_data))
        prediction_total = linear_regression_total_model.predict(input_data)
        emit('prediction_result', {'time': prediction_time, 'total': prediction_total[0]})
        
@socketio.on('test_event')
def handle_test_event(data):
    emit('test_response', {'message': 'Test event received!'})
    
    
    

if __name__ == '__main__':
    socketio.run(app, debug=True, use_reloader=True, log_output=True, port=5000, allow_unsafe_werkzeug=True)
