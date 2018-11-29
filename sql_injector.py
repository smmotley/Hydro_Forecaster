"""
Data Extraction and Plotting for various Weather APIs
===========================

"""
import pandas as pd
import datetime
import numpy as np
#from datetime import datetime
from datetime import timedelta
from dateutil import parser
import pytz
from pandas.io.json import json_normalize
import matplotlib as mpl
import matplotlib.pyplot as plt

from matplotlib import cm
import time
import os
import sqlite3

from requests.exceptions import HTTPError

plt.interactive(False)
#KEYS = pd.read_csv(os.path.join(Path(__file__).parents[2], 'userkeys.config'))
#n = NOAA()

class MplColorHelper:

    def __init__(self, cmap_name, start_val, stop_val):
        self.cmap_name = cmap_name
        self.cmap = plt.get_cmap(cmap_name)
        self.norm = mpl.colors.Normalize(vmin=start_val, vmax=stop_val)
        self.scalarMap = cm.ScalarMappable(norm=self.norm, cmap=self.cmap)

    def get_rgb(self, val):
        return self.scalarMap.to_rgba(val)


def main():
    create_actual_metered_flows_table()
    #create_flows_table()
    #create_actual_flows_table()
    #cnrfc_datapull()
    #cleanup_meter_data()
    metered_data_datapush()


def lsp_datapull():
    today = datetime.now()
    sensors = {
        'hourly_precip' : 16,
        'hourly_temp' : 30
    }
    data = n.historical_data(today - timedelta(days=7), today)
    df_hist = pd.concat([pd.DataFrame(json_normalize(x)) for x in data], ignore_index=True)
    #df_hist.drop(['SENSOR_NUM', 'sensorType'], axis=1, inplace=True)

    df_hist = pd.merge(df_hist[df_hist.SENSOR_NUM != 30], df_hist[df_hist.SENSOR_NUM != 16],
                       on=['date','stationId','durCode'], how='left', suffixes=('_rain', '_temp'))
    df_hist.drop(['dataFlag_rain','dataFlag_temp','obsDate_rain','obsDate_temp'], axis=1, inplace=True)
    df_hist.rename(columns={'stationId': 'station_id', 'value_rain': 'precip', 'value_temp':'temperature'}, inplace=True)
    df_hist['date'] = pd.to_datetime(df_hist['date'])
    df_hist.set_index("date", inplace=True)
    return df_hist

def cnrfc_datapull():
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    date_list = [datetime.now() - timedelta(days=x) for x in range(0,(365*2)-55)]
    for date in date_list[::-1]:
        file_date = date.strftime("%Y%m%d")
        file_url = 'http://www.cnrfc.noaa.gov/csv/'+file_date+'12_american_csv_export.zip'
        try:
            df = pd.read_csv(file_url, skiprows=[1], compression='zip')
        except Exception:
            print("COULD NOT GET FORECAST FOR " + date.strftime("%Y-%m-%d"))
            continue
        else:
            df['GMT'] = pd.to_datetime(df['GMT'])
            df['date_created'] = date.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=None)
            df.rename(columns={"GMT" : "date_valid"}, inplace=True)
            # Drop MFAC1.1 (not sure what it is). If it doesn't exist in the df, don't error out, just ignore it.
            df.drop(columns=['MFAC1.1'], inplace=True, errors='ignore')
            df['R20_Est'] = df['MFAC1L'] - df['RUFC1'] - df['NMFC1']
            df_historical =  df.loc[(df.date_valid < df.date_created)]
            df_forecast = df[(df.date_valid >= df.date_created)]

            historical_columns = ','.join(list(df_historical))
            df_historical.to_sql('temporary_table', conn, if_exists='replace', index=False)
            c.execute("INSERT OR IGNORE INTO cnrfc_actuals(%s) SELECT * from temporary_table" % (historical_columns))

            forecast_columns = ','.join(list(df_forecast))
            df_forecast.to_sql('temporary_table', conn, if_exists='replace', index=False)
            c.execute("INSERT OR IGNORE INTO cnrfc_fcst(%s) SELECT * from temporary_table" % (forecast_columns))
            print("Done with forecast for " + date.strftime("%Y-%m-%d"))


        #df_historical.to_sql('cnrfc_actuals', conn, if_exists='append', index=False)
        #df_forecast.to_sql('cnrfc_fcst', conn, if_exists='append', index=False)
    return
def metered_data_datapush():
    file_path = "G:\Shared Files\Power Marketing\Data Source\Hydrology\Streamgage"
    file_years = ["WY2018"]
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    df_stations = pd.DataFrame()
    for fy in file_years:
        fp = os.path.join(file_path,fy)
        for file in os.listdir(fp):
            if file.endswith('.xlsx') and file.startswith("R"):
                station = (file.split('.')[0]).replace('-',"")
                df = pd.read_excel(os.path.join(file_path,fy,file), header=1)
                print("Pulling data for: " + station)
                df.loc[df['Time'] == datetime.datetime(1900,1,1,0,0), 'Time'] = datetime.time(0,0)
                df['date_valid'] = df["Date"] + pd.to_timedelta(df['Time'].astype(str))
                df.drop(["Date","Time","Ght","Shift","ght"], axis=1, inplace=True, errors='ignore')
                df.rename(columns={'Q': station, 'AF': station}, inplace=True)
                if df_stations.empty:
                    df_stations = df
                else:
                    df_stations = pd.merge(df_stations, df[[station, 'date_valid']], on='date_valid', how='left')
        df_stations.to_sql('metered_actuals', conn, if_exists='append', index=False)



    c.close()
    return

def cleanup_meter_data():
    file_path = "G:\Shared Files\Power Marketing\Data Source\Hydrology\Streamgage"
    file_years = ['WY2013', 'WY2014', 'WY2015', 'WY2016', 'WY2017', 'WY2018']
    for fy in file_years:
        fp = os.path.join(file_path, fy)
        for file in os.listdir(fp):
            if file.endswith('.xlsx'):
                station = (file.split('.')[0]).replace('-', "")
                station = (file.split('.')[0]).replace('-', "")
                df = pd.read_excel(os.path.join(file_path, fy, file), header=1)
                for row in df.itertuples():
                    if not isinstance(row.Time, datetime.time):
                        badVal = (row.Time).split(" ")
                        df.loc[row.Index, 'Time'] = badVal[0] + ":00"
                        df.loc[row.Index, 'GHT'] = (int(badVal[-1]) * 10) + df.loc[row.Index, 'GHT']
                    if isinstance(row.Shift, str):
                        badVal = (row.Shift).split(" ")
                        df.loc[row.Index, 'Shift'] = badVal[0]
                        if isinstance(df.loc[row.Index, 'Q'], str):
                            oldVal = df.loc[row.Index, 'Q'].replace(",","")
                            newVal = int(oldVal)
                        df.loc[row.Index, 'Q'] = badVal[-1] * 10000 + newVal



# National water model
def nwm_datapull():
    today = datetime.now()

def historical(cities,date):
    hist = n.historical_data(date)
    df_hist = pd.concat([pd.DataFrame(json_normalize(x['properties'])) for x in hist['features']], ignore_index=True)
    df_hist = df_hist[df_hist['station'].isin(cities)]

    # Need to convert list objects to strings since SQL can not take a list
    df_hist["high_record_years"] = df_hist["high_record_years"].apply(lambda x: list(map(str, x)), 1).str.join(',')
    df_hist["low_record_years"] = df_hist["low_record_years"].apply(lambda x: list(map(str, x)), 1).str.join(',')
    df_hist["date"] = date
    df_hist.set_index("date", inplace=True)
    return df_hist

def sql_inject(df, location, actuals):
    pd.options.mode.chained_assignment = None  # Turns off a warning that we are copying a dataframe
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Need to convert to tz-naive if injecting into sqlite (actuals have already been converted).
    if not actuals:
        df.index = df.index.tz_convert(None)

    # df.columns = [str(col) + '_Tmax' for col in df.columns]
    #df['stationId'] = location
    df['date_valid'] = df.index.astype('str')

    station = df['station_id'][0]
    data = [tuple(x) for x in df.values]
    wildcards = ','.join(['?'] * len(df.columns))

    c.executemany("INSERT OR IGNORE INTO actuals(station_id, temperature, precip, date_valid) "
              "VALUES (?, ?, ?, ?)",
              (data))

    conn.commit()
    c.close()
    conn.close()

    pd.options.mode.chained_assignment = 'warn'  # Turn warning back on
    return


def hourly(n, latlng, convert_to_daily):
    # 1) Grab the data from the interwebs
    res_nws = n.points_forecast(latlng[0], latlng[1], hourly=True)     # NWS POINT FORECAST
    res_wu = n.wu_forecast(latlng[0], latlng[1], hourly=True)          # Wunderground POINT FORECAST

    # 2) Make dataframe objects from json data
    # The WU forecast must be flattened to create dataframe.
    df_wu_hourly = pd.concat([pd.DataFrame(json_normalize(x)) for x in res_wu['hourly_forecast']], ignore_index=True)
    df_nws_hourly = pd.DataFrame(res_nws['properties']['periods'])

    # 3) Take the string object and convert to a datetime object.
    # Set the column FCTTIME.UTCDATE (which is currently empty) to the 'epoch' object in the json file.
    df_wu_hourly['FCTTIME.UTCDATE'] = [datetime.utcfromtimestamp(float(t['FCTTIME']['epoch'])) for t in res_wu['hourly_forecast']]

    # Make sure the column 'startTime' is a datetime object for Pandas to read
    df_nws_hourly['startTime'] = pd.to_datetime(df_nws_hourly['startTime'])

    # 4) Convert times to timezone aware objects
    # Provide timezone information to our dataframe by first setting the time information to UTC.
    df_wu_hourly['FCTTIME.UTCDATE'] = df_wu_hourly['FCTTIME.UTCDATE'].dt.tz_localize(pytz.utc)

    # Create a dataframe for the NWS forecast, make this timezone aware by first setting it to UTC.
    df_nws_hourly['startTime'] = df_nws_hourly['startTime'].dt.tz_localize(pytz.utc)

    # 5) Now that we have two dataframes, both with datetime columns in UTC,
    #   we can merge them based off the datetime column.
    df_fcst_hourly = pd.merge(df_wu_hourly, df_nws_hourly, left_on='FCTTIME.UTCDATE',right_on='startTime', how='left')
    df_fcst_hourly[['temp.english','dewpoint.english']]=df_fcst_hourly[['temp.english','dewpoint.english']].apply(pd.to_numeric)

    # 6) We now have one dataframe, in UTC. Convert datetime to local time before resampling from hourly to daily.

    # Get timezone information. NOTE, we are using timezone info from NWS only since
    #  the locations of the WU and NWS are the same.
    parsedDate = parser.parse(res_nws['properties']['periods'][0]['startTime'])

    df_fcst_hourly['FCTTIME.UTCDATE'] = df_fcst_hourly['FCTTIME.UTCDATE'].dt.tz_convert(parsedDate.tzinfo)
    df_fcst_hourly.set_index('FCTTIME.UTCDATE',inplace=True)

    df_fcst_hourly.rename(columns = {'temp.english' : 'wu_temp', 'temperature' : 'nws_temp'}, inplace=True)
    # This was just a test to prove that the resampling of hourly data to daily data would keep everything
    # in the correct timezone
    # df_fcst_hourly.at['2018-07-22T21:00:00.000000000','nws_temp'] = 115

    df_fcst_hourly.plot(y=['wu_temp', 'nws_temp'], use_index= True, kind='line')

    #plt.show()

    # 7) Resample hourly data into daily data based off of local timezone information
    df_fcst_daily = df_fcst_hourly.resample('D')['wu_temp','nws_temp'].agg({'min','max'})

    # If you don't joint the columns names, the names will be a tuple which is difficult to access
    df_fcst_daily.columns = ['_'.join(col).strip() for col in df_fcst_daily.columns.values]
    if convert_to_daily:
        return df_fcst_daily
    return df_fcst_hourly


def daily(n, latlng):
    # 1) Get json data from NWS and WU response. We are getting daily data here, so set hourly flag to FALSE
    res_nws = n.points_forecast(latlng[0], latlng[1], hourly=False)  # NWS POINT FORECAST
    res_wu = n.wu_forecast(latlng[0], latlng[1], hourly=False)  # Wunderground POINT FORECAST

    # 2) Make dataframe object from the json response
    # Make a dataframe object of the WU forecast by flattening out the json file.
    df_wu = pd.concat([pd.DataFrame(json_normalize(x)) for x in res_wu['forecast']['simpleforecast']['forecastday']], ignore_index=True)
    try:
        df_nws = pd.DataFrame(res_nws['properties']['periods'])
    except KeyError:
        print("!!!!FATAL ERROR!!!! NWS Data Unavailable: " + res_nws['detail'])
        exit()
    # 3) Take the string object and convert to a datetime object.
    #   Set the column 'day' to the 'epoch' object in the json file.
    #   Since the NWS must match these dates, we just use WU dates.
    df_wu['day'] = [datetime.utcfromtimestamp(float(t['date']['epoch'])) for t in res_wu['forecast']['simpleforecast']['forecastday']]

    # 4) Get time zone data and convert any datetime columns to datetime objects that Pandas can read.
    # Get the timezone location for our point from Wunderground's json file.
    wu_timezone = res_wu['forecast']['simpleforecast']['forecastday'][0]['date']['tz_long']
    nws_timezone = parser.parse(res_nws['properties']['periods'][0]['startTime'])

    # Provide timezone information to our dataframe by first setting the time information to UTC,
    # then converting to the actual timezone
    df_wu['day'] = df_wu['day'].dt.tz_localize(pytz.utc)
    df_wu['day'] = df_wu['day'].dt.tz_convert(wu_timezone)
    df_wu.rename(columns={'high.fahrenheit': 'high_wu', 'low.fahrenheit': 'low_wu'}, inplace=True)
    df_wu[['high_wu', 'low_wu']]=df_wu[['high_wu', 'low_wu']].apply(pd.to_numeric)

    # Make sure the time columns are a datetime object for Pandas to read
    df_nws['startTime'] = pd.to_datetime(df_nws['startTime'], utc=True)
    df_nws['startTime'] = df_nws['startTime'].dt.tz_convert(nws_timezone.tzinfo)
    df_nws['endTime'] = pd.to_datetime(df_nws['endTime'], utc=True)
    df_nws['endTime'] = df_nws['endTime'].dt.tz_convert(nws_timezone.tzinfo)

    # 5) NWS Only: There is no "high" or "low" column in the data, so we have to create one:
    # Instead of combining the data by a single day, the NWS provides a start and end
    # time for each period with an "isDaytime" flag. We will use the isDaytime flag to get
    # the daytime and nighttime temperaures.
    df_nws['high_nws'] = df_nws[df_nws.isDaytime.isin([True])]['temperature']
    df_nws['low_nws'] = df_nws[df_nws.isDaytime.isin([False])]['temperature']

    # We want to merge the dataframes off of a unique date, but the NWS data has the same date
    # muliple times. Therefore, we will just make a "day and night" dataframe that has only one day
    # per entry, which will allow us to merge that data with the wUnderground data.
    df_nws_day = df_nws[pd.notnull(df_nws['high_nws'])]
    df_nws_night = df_nws[pd.notnull(df_nws['low_nws'])]

    # 6) Merge the two dataframes twice: Once to get the NWS high temperatures into the df and once to get the low
    # temperatures. After this is done, we have one dataframe that we can return.
    df_wu = pd.merge(df_wu, df_nws_day[['high_nws']], left_on=[df_wu.day.dt.month,df_wu.day.dt.day],
                      right_on=[df_nws_day['endTime'].dt.month, df_nws_day['endTime'].dt.day], how='left')

    # for some reason, the merge puts in a key_0, key_1 col, which needs to be deleted before we do the next merge.
    df_wu.drop(['key_0','key_1'], axis = 1 ,inplace = True)

    df_wu = pd.merge(df_wu, df_nws_night[['low_nws']], left_on=[df_wu.day.dt.month, df_wu.day.dt.day],
                        right_on=[df_nws_night['endTime'].dt.month, df_nws_night['endTime'].dt.day], how='left')

    # for some reason, the merge puts in a key_0, key_1 col, which needs to be deleted before we do the next merge.
    df_wu.drop(['key_0', 'key_1'], axis=1, inplace=True)

    df_wu.set_index('day', inplace=True)
    # Note: even though the df_wu will display in UTC if you view the df, it is still timezone aware and
    #       will contain info for the correct timezone (prove it by uncommenting the print statement below).
    # print(df_wu.index[0].day)
    return df_wu

def stormVista(cities):

    base_url = "https://www.stormvistawxmodels.com/"
    clientKey =  KEYS.iloc[0]['key']
    models = ["gfs", "ecmwf", "gfs-ens-bc", "ecmwf-eps"]
    # hours = np.arange(0,360,6)
    today = datetime.utcnow()
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y%m%d")

    modelCycle = '12z'
    # General rule that the 12Z model is not out until roughly 1:00 pm PDT (20z)
    # and the 00Z isn't avail until 1:00 am (0800Z)
    if 8 <= today.hour <= 20:
        modelCycle = '00z'

    # Create and empty dataframe that will hold dates in the ['date'] column for 16 days.
    df_models = pd.DataFrame(data=pd.date_range(start=today.strftime("%Y%m%d"), periods=16, freq='D'), columns=['date'])

    for model in models:
        # raw = "client-files/" + clientKey + "/model-data/" + model + "/" + today + "/" +
        # modelCycle + "/city-extraction/individual/" + regions + "_raw.csv"
        #CORRECTED:
        #sv_min_max = "client-files/" + clientKey + "/model-data/" + model + "/" + today.strftime("%Y%m%d") + "/" + modelCycle + "/city-extraction/corrected-max-min_northamerica.csv"

        #RAW
        sv_min_max = "client-files/" + clientKey + "/model-data/" + model + "/" + today.strftime(
            "%Y%m%d") + "/" + modelCycle + "/city-extraction/max-min_northamerica.csv"
        fileName = today.strftime("%Y%m%d") + "_" + modelCycle + "_" + model + ".csv"

        curDir = os.path.dirname(os.path.abspath(__file__))
        # Download file if it hasn't been downloaded yet.
        if not os.path.isfile(os.path.join(curDir,fileName)):
            try:
                df_min_max = pd.read_csv(base_url + sv_min_max, header=[0, 1])
                time.sleep(5)  # Wait 5 seconds before continuing (per stormvista api requirement)
                df_min_max.to_csv(os.path.join(curDir,fileName), index=False)
            except:
                return pd.DataFrame(data=pd.date_range(start=today,
                                             end=(datetime.utcnow() + timedelta(days=15)).strftime("%Y%m%d"),
                                                       freq='D'), columns=['date'])
        else:
            df_min_max = pd.read_csv(os.path.join(curDir, fileName), header=[0, 1])

        # Because the header info is in the top two rows, pandas treats each column name as a tuple. Flatten the
        # tuple and put a "/" between each string (column 1 = tuple ("A","B") => "A/B"
        df_min_max.columns = df_min_max.columns.map('/'.join)
        df_min_max.set_index(['station/station'], inplace=True)

        #The first 4 charactors in the string will be either "max/" or "min/" followed by the date.
        dates = [c[:-4] for c in df_min_max.columns]
        df = pd.DataFrame(data=pd.date_range(start=dates[0],
                                             end=dates[-1], freq='D'), columns=['date'])

        df_mins = df_min_max[[col for col in df_min_max if 'min' in col]]
        df_maxs = df_min_max[[col for col in df_min_max if 'max' in col]]

        df_mins.columns = [pd.to_datetime(c[:-4]) for c in df_mins.columns]
        df_maxs.columns = [pd.to_datetime(c[:-4]) for c in df_maxs.columns]

        # df_min = pd.DataFrame(data=df_mins.loc[['KSAC', 'KBLU']].T)
        df_min = pd.DataFrame(data=df_mins.loc[cities].T)
        df_min.index.name = 'date'
        df_min.columns = [city + "_min_" + model for city in df_min.columns]

        df_max = pd.DataFrame(data=df_maxs.loc[cities].T)
        df_max.index.name = 'date'
        df_max.columns = [city + "_max_" + model for city in df_max.columns]

        df_models = pd.merge(df_models, df_min, on='date', how='left')
        df_models = pd.merge(df_models, df_max, on='date', how='left')

        # dates = [c for c in df_min_max.columns if c[-2:] != '.1' and c != 'station']
        # df_min_max.set_index(['station_station'], inplace=True)

    getEnsMembers = False
    if getEnsMembers == True:
        dates = list(map(lambda t: (datetime.now() + timedelta(days=t)).strftime("%Y%m%d"), range(15)))
        model = 'ecmwf-eps'
        ens_var = 'tmp2m'
        for date in dates:
            ens_corrected = "client-files/" + clientKey + "/model-data/" + model + "/" + today + "/" + modelCycle + "/city-extraction/d" + today + "_corrected_members_" + ens_var + "_northamerica_06z-06z.csv"
            df_ens = pd.read_csv(base_url+ens_corrected)
    df_models['date'] = df_models['date'].dt.tz_localize(pytz.utc)
    df_models.set_index('date', inplace=True)
    return df_models

def create_actuals_table(c):
    # The unique clause will ensure that, for a given station,
    c.execute("CREATE TABLE IF NOT EXISTS actuals("
                "date_valid DATETIME , "
                "station_id TEXT, "
                "temperature REAL, "
                "precip REAL, "
                "UNIQUE(date_valid, station_id))")
    return

def create_flows_table():
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # The unique clause will ensure that, for a given station,
    c.execute("CREATE TABLE IF NOT EXISTS cnrfc_fcst("
                "date_valid DATETIME , "
                "date_created DATETIME , "
                 "NFDC1 REAL,"
                "FMDC1 REAL,"
                "FMDC1O REAL,"
                "BCTC1 REAL,"
                "LNLC1 REAL,"
                "RRGC1 REAL,"
                "HLLC1 REAL,"
                "HLLC1F REAL,"
                "NMFC1 REAL,"
                "RUFC1 REAL,"
                "MFAC1 REAL,"
                "MFAC1F REAL,"
                "UNVC1F REAL,"
                "ICHC1 REAL,"
                "AKYC1 REAL,"
                "AKYC1F REAL,"
                "CBAC1 REAL,"
                "CBAC1F REAL,"
                "FOLC1 REAL,"
                "FOLC1R REAL,"
                "FOLC1F REAL,"
                "UNVC1 REAL,"
                "SVCC1 REAL,"
                "MFAC1L REAL,"
                "CBAC1L REAL,"
                "RBBC1F REAL,"
                "RBBC1 REAL,"
                "RBBC1SPL REAL,"
                "LNLC1F REAL,"
                "RRGC1L REAL,"
                "RRGC1F REAL,"
                "RUFC1L REAL,"
                "SVCC1F REAL,"
                "SVCC1L REAL,"
                "HLLC1L REAL,"
                "HLLC1SPL REAL,"
                "R20_Est REAL, "
                "UNIQUE(date_created, date_valid))")
    return

def create_actual_flows_table():
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # The unique clause will ensure that, for a given station,
    c.execute("CREATE TABLE IF NOT EXISTS cnrfc_actuals("
                "date_valid TIMESTAMP , "
                "date_created TIMESTAMP , "
                "NFDC1 REAL,"
                "FMDC1 REAL,"
                "FMDC1O REAL,"
                "FOLC1R REAL,"
                "BCTC1 REAL,"
                "LNLC1 REAL,"
                "RRGC1 REAL,"
                "HLLC1 REAL,"
                "HLLC1F REAL,"
                "NMFC1 REAL,"
                "RUFC1 REAL,"
                "MFAC1 REAL,"
                "MFAC1F REAL,"
                "UNVC1F REAL,"
                "ICHC1 REAL,"
                "AKYC1 REAL,"
                "AKYC1F REAL,"
                "CBAC1 REAL,"
                "CBAC1F REAL,"
                "FOLC1 REAL,"
                "FOLC1F REAL,"
                "UNVC1 REAL,"
                "SVCC1 REAL,"
                "MFAC1L REAL,"
                "CBAC1L REAL,"
                "RBBC1F REAL,"
                "RBBC1 REAL,"
                "RBBC1SPL REAL,"
                "LNLC1F REAL,"
                "RRGC1L REAL,"
                "RRGC1F REAL,"
                "RUFC1L REAL,"
                "SVCC1F REAL,"
                "SVCC1L REAL,"
                "HLLC1L REAL,"
                "HLLC1SPL REAL,"
                "R20_Est REAL, "
                "UNIQUE(date_valid))")
    return

def create_actual_metered_flows_table():
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # The unique clause will ensure that, for a given station,
    c.execute("CREATE TABLE IF NOT EXISTS metered_actuals("
                "date_valid TIMESTAMP , "
                "R1 REAL,"
                "R2 REAL,"
                "R3 REAL,"
                "R4 REAL,"
                "R5 REAL,"
                "R5L REAL,"
                "R6 REAL,"
                "R7 REAL,"
                "R8 REAL,"
                "R10 REAL,"
                "R11 REAL,"
                "R12 REAL,"
                "R13 REAL,"
                "R15 REAL,"
                "R16 REAL,"
                "R20 REAL,"
                "R22 REAL,"
                "R23 REAL,"
                "R24 REAL,"
                "R27 REAL,"
                "R28 REAL,"
                "R29 REAL,"
                "R30 REAL,"
                "R31 REAL,"
                "UNIQUE(date_valid))")
    return

if __name__ == "__main__":
    main()
