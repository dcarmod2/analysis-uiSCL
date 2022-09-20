#!/usr/bin/env python
# coding: utf-8

import geopandas as gpd
import pandas as pd
import json
import numpy as np
import os
from natsort import natsorted
from zipfile import ZipFile,ZIP_DEFLATED
from os.path import exists
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import json
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, UnexpectedAlertPresentException, StaleElementReferenceException

STOCKHOLM_PROJ='EPSG:5850'
UNPROJECT='EPSG:4326'
START_TIME = 21600 # seconds since midnight; 21600 is 6 am 
WINDOW = 300
PROJECT_NAME = "default"
PROJECT_ID = "631e1da5345cc2539e276854"
FILES_TO_DO = set([])

ANALYSIS_REQUEST = """
{{
  "accessModes": "WALK",
  "bikeSpeed": 4.166666666666667,
  "bikeTrafficStress": 4,
  "date": "2020-12-12",
  "decayFunction": {{
    "type": "step",
    "standardDeviationMinutes": 10,
    "widthMinutes": 10
  }},
  "destinationPointSetIds": [],
  "directModes": "WALK",
  "egressModes": "WALK",
  "fromTime": 25200,
  "maxBikeTime": 20,
  "maxRides": 4,
  "maxWalkTime": 20,
  "monteCarloDraws": 200, 
  "percentiles": [
    5,
    25,
    50,
    75,
    95
  ],
  "toTime": 32400,
  "transitModes": "BUS,TRAM,RAIL,SUBWAY,FERRY,CABLE_CAR,GONDOLA,FUNICULAR",
  "walkSpeed": 1.3888888888888888,
  "workerVersion": "v6.0.1",
  "variantIndex": -1,
  "projectId": "{}",
  "bounds": {{
    "south": {},
    "west": {},
    "north": {},
    "east": {}
  }},
  "fromLat": {},
  "fromLon": {},
  "recordTimes": true,
  "recordPaths": true,
  "toLat": 59.31834561522184,
  "toLon": 18.071908950805668,
  "name": "{}"
}}
"""

TEST_REQUEST = """
{{
  "accessModes": "WALK",
  "bikeSpeed": 4.166666666666667,
  "bikeTrafficStress": 4,
  "date": "2020-12-12",
  "decayFunction": {{
    "type": "step",
    "standardDeviationMinutes": 10,
    "widthMinutes": 10
  }},
  "destinationPointSetIds": [],
  "directModes": "WALK",
  "egressModes": "WALK",
  "fromTime": 25200,
  "maxBikeTime": 20,
  "maxRides": 4,
  "maxWalkTime": 20,
  "monteCarloDraws": 200,
  "percentiles": [
    5,
    25,
    50,
    75,
    95
  ],
  "toTime": 32400,
  "transitModes": "BUS,TRAM,RAIL,SUBWAY,FERRY,CABLE_CAR,GONDOLA,FUNICULAR",
  "walkSpeed": 1.3888888888888888,
  "workerVersion": "v6.0.1",
  "variantIndex": -1,
  "projectId": "{}",
  "fromLat": {},
  "fromLon": {},
  "recordTimes": true,
  "recordPaths": true,
  "toLat": 59.31834561522184,
  "toLon": 18.071908950805668,
  "name": "{}"
}}
"""

grid_files = natsorted([x for x in os.listdir('../lib/actions/analysis/') if x.startswith('stock_nowater_pairs_400')])
grid_gdfs = [json.load(open('../lib/actions/analysis/' + x))["pairs"] for x in grid_files]
grid_xy = [np.mean(points, axis=0) for points in grid_gdfs]
grid_bounds = [np.append(np.amax(points, axis=0), np.amin(points, axis=0)) for points in grid_gdfs]
assert(len(grid_xy) == len(grid_bounds))

def toRad(value):
    return value * np.pi / 180;

def haversine(lat1,lon1,lat2,lon2):
    R = 6371
    latDistance = toRad(lat2-lat1)
    lonDistance = toRad(lon2-lon1)
    a = np.sin(latDistance / 2) * np.sin(latDistance / 2) + np.cos(toRad(lat1)) * np.cos(toRad(lat2)) * np.sin(lonDistance / 2) * np.sin(lonDistance / 2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    distance = R * c * 1000
    return distance

gtf_dir = 'gtfs/'
routes = pd.read_csv(gtf_dir+'routes.txt')
trips = pd.read_csv(gtf_dir+'trips.txt')
shapes = pd.read_csv(gtf_dir+'shapes.txt')
stops = pd.read_csv(gtf_dir+'stops.txt')
stop_times = pd.read_csv(gtf_dir+'stop_times.txt')
stops_re = stops.set_index('stop_id')


class stop_remover:
    
    def __init__(self,stops,stop_times,trips,lat,lon):
        self.stops = stops
        self.stop_times = stop_times
        self.trips = trips
        self.lat = lat
        self.lon = lon
        self.nearby_stops = None
        self.removed_stop_locs = None
        self.trip_ids_tp_remove = None
        
    def get_nearby_stops(self):
        nearby_stops = []
        for idx,(stoplat,stoplon) in self.stops.loc[:,['stop_lat','stop_lon']].iterrows():
            if haversine(self.lat,self.lon,stoplat,stoplon) < 2000:
                nearby_stops.append(self.stops.loc[idx,'stop_id'])
        self.nearby_stops = nearby_stops
        removed_stop_locs = self.stops.set_index('stop_id').loc[self.nearby_stops,['stop_lon','stop_lat']].values
        self.removed_stop_locs = removed_stop_locs
        return nearby_stops
    
    def removed_stops_to_file(self,filename):
        
        gpd.GeoSeries(gpd.points_from_xy(self.removed_stop_locs[:,0],self.removed_stop_locs[:,1])).to_file(filename,driver='GeoJSON')
    
    @staticmethod
    def get_centroid(arr):
        x_cent = np.mean(arr[:,0])
        y_cent = np.mean(arr[:,1])
        return np.array([x_cent,y_cent])

    
    def nearest_gridpt(self,gridlocs):
        arr_cent = self.get_centroid(self.removed_stop_locs)
        return np.argmin([np.linalg.norm(x-arr_cent) for x in gridlocs])
    
    
    def is_removed(self,x):
        return x in self.nearby_stops
    
    def clean_trips(self):
        self.trip_ids_to_remove = set(self.stop_times[self.stop_times['stop_id'].map(self.is_removed)]['trip_id'].values)
        
    

def get_edited_times(sr):
    def not_removed(x):
        return not sr.is_removed(x)
    return stop_times[stop_times['stop_id'].map(not_removed)]

def create_edited_times(lat,lon):
    sr = stop_remover(stops,stop_times,trips,lat,lon)
    sr.get_nearby_stops()
    stop_times_edited = get_edited_times(sr)
    stop_times_edited.to_csv('edited_gtfs/stop_times.txt',index=False)
    return sr

def write_gtfs(name):
    with ZipFile(name, 'w',compression=ZIP_DEFLATED) as myzip:
        for file in os.listdir('edited_gtfs'):
            myzip.write(f'edited_gtfs/{file}')
        
def safeClick(path, wait_time = 10):
    for _ in range(2):
        try:
            # driver.find_element(by=By.XPATH, value=path).click()
            WebDriverWait(driver,wait_time).until(EC.element_to_be_clickable((By.XPATH, path))).click()
            return
        except (UnexpectedAlertPresentException, AttributeError) as e:
            driver.switch_to.alert.accept()
        except (StaleElementReferenceException, TimeoutException) as e:
            print("")
        print(f"clicking {path} again")

def safeWait(path, wait_time = 10):
    for _ in range(2):
        try:
            # driver.find_element(by=By.XPATH, value=path).click()
            WebDriverWait(driver,wait_time).until(EC.presence_of_element_located((By.XPATH, path))).click()
            return
        except (UnexpectedAlertPresentException, AttributeError) as e:
            driver.switch_to.alert.accept()
        except (StaleElementReferenceException, TimeoutException) as e:
            print("")
        print(f"trying {path} again")

def removeOthers():
    safeClick('//div[@id="sidebar"]//div[@title="Projects"]')

# For each region, find the most popular stop
def removeStop(i):
    print(f"process for {i}")
    centerLat, centerLon = grid_xy[i]
    maxLon, maxLat, minLon, minLat = grid_bounds[i]
    if exists(f'removed_stops/rm_{i}.json'):
        return

    # Compute the most popular stop in this area 
    safeClick('//div[@id="sidebar"]//div[@title="Analyze"]')
    safeClick('//div[@id="PrimaryAnalysisSettings"]//button[@title="expand"]')
    safeClick('//div[@role="tablist"]//button[@title="Custom JSON editor"]')
    textArea = driver.find_element(by=By.ID, value="customProfileRequest")
    textArea.clear()
    textArea = driver.find_element(by=By.ID, value="customProfileRequest")
    textArea.send_keys(ANALYSIS_REQUEST.format(PROJECT_ID, minLat, minLon, maxLat, maxLon, centerLat, centerLon, f"stock_nowater_400_{i}"))
    time.sleep(5)
    safeClick('//button[@title="Fetch results"]')
    try:
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.ID, 'popularStops')))    
    except TimeoutException:
        print("Skipping %s because no stops", i) # skip this region, as there are no stops in it 
        return

    popLat, popLon = driver.find_element(by=By.ID, value="popularStops").get_attribute("innerHTML").split(",")
    print(f"Got stop {popLat}, {popLon}; Modifying GTFS file to remove.")

    # Remove existing stop_times.txt
    if os.path.exists("./edited_gtfs/stop_times.txt"):
        os.remove("./edited_gtfs/stop_times.txt")
    else:
        print("stop_times.txt does not exist")

    sr = create_edited_times(float(popLat),float(popLon))
    write_gtfs(f'edited_gtfs_files/edited_gtfs_{i}.zip')
    sr.nearest_gridpt(grid_xy)

    sr.removed_stops_to_file(f'removed_stops/rm_{i}.json')


### Create isochrone for each ###
def createIsochrone(i):
    print(f"Creating isochrone for {i}")
    centerLat, centerLon = grid_xy[int(i)]

    ### Create a new network bundle if doesn't alreaday exist ###
    safeClick('//div[@id="sidebar"]//div[@title="Network Bundles"]')
    try:
        driver.find_element(by=By.XPATH, value='//*[@id="selectBundle"]/ancestor::div[3]').click()
        driver.find_element(by=By.XPATH, value=f'//div[text()="{i}"]').click()
    except NoSuchElementException: 
        safeClick('//button[text()="Create a new network bundle"]')
        driver.find_element(by=By.ID, value="bundleName").send_keys(f"{i}")
        dropdown = Select(driver.find_element(by=By.ID, value="osmId"))
        dropdown.select_by_visible_text("default") # TODO: cleanup, this is a req
        safeClick('//button[text()="Upload new GTFS"]')
        driver.find_element(by=By.ID, value="feedGroup").send_keys(f'/Users/ophzhu/urop_conveyal/analysis-uiSCL/scripts/edited_gtfs_files/edited_gtfs_{i}.zip')
        safeClick('//button[text()="Create"]')
        safeWait('//h2[text()="Edit bundle"]', wait_time=60)   

    ### Create new project ###
    safeClick('//div[@id="sidebar"]//div[@title="Projects"]')
    try:
        driver.find_element(by=By.XPATH, value=f'//div[@id="innerdock"]//button[text()="{i}"]').click()
    except NoSuchElementException:
        safeClick('//button[text()="Create new Project"]')
        # Type project name
        nameLabel = driver.find_element(by=By.XPATH, value='//label[text()="Project name"]')
        driver.find_element(by=By.ID, value=nameLabel.get_attribute("for")).send_keys(f"{i}")
        # Select associated network bundle 
        safeClick('//div[contains(@class, "indicatorContainer")]')
        safeClick(f'//div[text()="{i}"]')
        safeClick('//button[text()="Create"]')
    time.sleep(5)
    print(driver.current_url)
    projectId = driver.current_url.split("/")[6]

    ### Create isochrones ###
    # Go to test tab and switch first one to default, second to modified network
    safeClick('//div[@id="sidebar"]//div[@title="Test"]')
    safeClick('//div[@id="PrimaryAnalysisSettings"]//button[@title="expand"]')
    projectLabel = driver.find_element(by=By.XPATH, value='//label[text()="Project"]')
    safeClick(f'//div[@id="{projectLabel.get_attribute("for")}"]//div[contains(@class, "indicatorContainer")]')
    safeClick(f'//div[text()="default"]')
    safeClick('//div[@role="tablist"]//button[@title="Custom JSON editor"]')
    driver.find_element(by=By.XPATH, value='//textarea[@id="customProfileRequest"]').send_keys(Keys.COMMAND + "a")
    driver.find_element(by=By.XPATH, value='//textarea[@id="customProfileRequest"]').send_keys(Keys.DELETE)
    driver.find_element(by=By.XPATH, value='//textarea[@id="customProfileRequest"]').send_keys(TEST_REQUEST.format(projectId, centerLat, centerLon, f"stock_nowater_pairs_400_{i}"))
    safeClick('//button[@title="Fetch results"]')
    WebDriverWait(driver,600).until(EC.presence_of_element_located((By.XPATH, '//button[@title="Fetch results"]'))).click()

    # Delete project and network bundle
    safeClick('//div[@id="sidebar"]//div[@title="Projects"]')
    safeClick(f'//div[@id="innerdock"]//button[text()="{i}"]')
    safeClick(f'//button[@aria-label="Edit project settings"]')
    safeClick(f'//button[text()="Delete project"]')
    safeClick(f'//button[contains(text(), "Confirm")]')
    safeClick('//div[@id="sidebar"]//div[@title="Network Bundles"]')
    safeClick('//*[@id="selectBundle"]/ancestor::div[3]')
    safeClick(f'//div[text()="{i}"]')
    safeClick(f'//button[text()="Delete this network bundle"]')
    safeClick(f'//button[contains(text(), "Confirm")]')


# selenium that uses the center as origin and finds the lat/lon of most popular stop
options = webdriver.ChromeOptions()
options.add_argument("--disable-popup-blocking")
options.add_argument("--force-device-scale-factor=1")
driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
driver.maximize_window()
driver.get("http://127.0.0.1:3000")
driver.implicitly_wait(10)
driver.find_element(by=By.XPATH, value='//button[text()="stockholm"]').click()

# el = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH, '//div[@id="innerdock"]//button[text()="{}"]'.format(PROJECT_NAME))))
# safeClick('//div[@id="innerdock"]//button[text()="{}"]'.format(PROJECT_NAME))
# for i in range(len(grid_xy)):
#     removeStop(i)

for file in natsorted(os.listdir("./edited_gtfs_files")):
    i = file.strip(".zip").split("_")[2]
    if i not in FILES_TO_DO:
    # if exists(f"/Users/ophzhu/Downloads/stock_nowater_pairs_400_{i}-25200-32400.json"):
        continue
    createIsochrone(i)

driver.quit()
