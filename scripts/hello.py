from cgitb import text
from os import remove
from os.path import exists
from tracemalloc import start
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import json
import glob
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, UnexpectedAlertPresentException, StaleElementReferenceException

### USING THE SCRIPT:
# Update the constants to the appropriate variables before using,
# namely PROJECT_NAME and PROJECT_ID. PROJECT_NAME is what you name the project and PROJECT_ID can be found in the URL 
# when you are in the Analysis tab with the project selected as the primary project 

# START_TIME can be changed if the script crashes in the middle of computing multiple time ranges
# Script can be modified in the beginning of the main code in order to detect which files already exist 
# to avoid recomputing files but is currently outdated 


START_TIME = 21600 # seconds since midnight; 21600 is 6 am 
WINDOW = 300
PROJECT_NAME = "default"
PROJECT_ID = "631e1da5345cc2539e276854"

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

# TEST_REQUEST = """
# {{
#   "accessModes": "WALK",
#   "bikeSpeed": 4.166666666666667,
#   "bikeTrafficStress": 4,
#   "date": "2020-12-12",
#   "decayFunction": {{
#     "type": "step",
#     "standardDeviationMinutes": 10,
#     "widthMinutes": 10
#   }},
#   "destinationPointSetIds": [],
#   "directModes": "WALK",
#   "egressModes": "WALK",
#   "fromTime": {},
#   "maxBikeTime": 20,
#   "maxRides": 4,
#   "maxWalkTime": 20,
#   "monteCarloDraws": 200,
#   "percentiles": [
#     5,
#     25,
#     50,
#     75,
#     95
#   ],
#   "toTime": {},
#   "transitModes": "BUS,TRAM,RAIL,SUBWAY,FERRY,CABLE_CAR,GONDOLA,FUNICULAR",
#   "walkSpeed": 1.3888888888888888,
#   "workerVersion": "v6.0.1",
#   "variantIndex": -1,
#   "projectId": "{}",
#   "fromLat": {},
#   "fromLon": {},
#   "recordTimes": true,
#   "recordPaths": true,
#   "toLat": 59.31834561522184,
#   "toLon": 18.071908950805668,
#   "name": "{}"
# }}
# """
TEST_REQUEST = """
{{
  "accessModes": "WALK",
  "bikeSpeed": 4.166666666666667,
  "bikeTrafficStress": 4,
  "bounds": {{
    "north": 59.45763913832078,
    "west": 17.75115966796875,
    "south": 59.19562559533593,
    "east": 18.2208251953125
  }},
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
  "fromLat": {},
  "fromLon": {},
  "recordTimes": true,
  "recordPaths": true,
  "toLat": 59.31834561522184,
  "toLon": 18.071908950805668,
  "name": "{}",
  "projectId": "{}"
}}
"""

"""
{"accessModes":"WALK","bikeSpeed":4.166666666666667,"bikeTrafficStress":4,"date":"2020-12-12","decayFunction":{"type":"step","standardDeviationMinutes":10,"widthMinutes":10},"destinationPointSetIds":[],"directModes":"WALK","egressModes":"WALK","fromTime":25200,"maxBikeTime":20,"maxRides":4,"maxWalkTime":20,"monteCarloDraws":200,"percentiles":[5,25,50,75,95],"toTime":32400,"transitModes":"BUS,TRAM,RAIL,SUBWAY,FERRY,CABLE_CAR,GONDOLA,FUNICULAR","walkSpeed":1.3888888888888888,"workerVersion":"v6.0.1","variantIndex":-1,"projectId":"63262801794e73312149e3f4","bounds":{"north":59.45763913832078,"south":59.19562559533593,"east":18.2208251953125,"west":17.75115966796875},"fromLat":59.326632366828356,"fromLon":17.985992431640625}
"""


def removeStop(jsonString):
    safeClick('//button[text()="Create a modification"]')

    nameLabel = driver.find_element(by=By.XPATH, value='//label[text()="Modification name"]')
    driver.find_element(by=By.ID, value=nameLabel.get_attribute("for")).send_keys("0")

    typeLabel = driver.find_element(by=By.XPATH, value='//label[text()="Transit modification type"]')
    dropdown = Select(driver.find_element(by=By.ID, value=typeLabel.get_attribute("for")))
    dropdown.select_by_visible_text("Remove Stops")

    safeClick('//button[text()="Create"]')
    # WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH, '//div[@role="tablist"]//button[@tabindex="-1"]')))    
    # time.sleep(5)
    safeClick('//div[@role="tablist"]//button[@aria-label="Edit JSON"]')
    textarea = driver.find_element(by=By.XPATH, value='//textarea[1]')
    textarea.clear()
    textarea.send_keys(jsonString)
    safeClick('//button[text()="Save custom changes"]')
    safeClick('//button[@aria-label="Modifications"]')

    return

def removeModifications():
    while True:
        try:
            stop = driver.find_element(by=By.XPATH, value='//div[@id="innerdock"]//button[contains(@aria-label, "Edit modification")]')
        except NoSuchElementException:
            break
        if stop == None:
            break
        safeClick('//div[@id="innerdock"]//button[contains(@aria-label, "Edit modification")]')
        safeClick('//button[@aria-label="Delete modification"]', 20) 
        safeClick('//footer[1]//button[not(contains(text(), "Cancel"))]')

def findCorners(filename):
    minLat, minLon = 200, 200
    maxLat, maxLon = -200, -200

    with open(filename) as json_file:
        data = json.load(json_file)
        for lon, lat in data["pairs"]:
            if lat > maxLat:
                maxLat = lat
            if lat < minLat:
                minLat = lat
            
            if lon > maxLon:
                maxLon = lon
            if lon < minLon:
                minLon = lon
        
    return minLat, minLon, maxLat, maxLon

def safeClick(path, wait_time = 10):
    for tries in range(2):
        try:
            # driver.find_element(by=By.XPATH, value=path).click()
            WebDriverWait(driver,wait_time).until(EC.element_to_be_clickable((By.XPATH, path))).click()
            return
        except (UnexpectedAlertPresentException, AttributeError) as e:
            driver.switch_to.alert.accept()
            continue
        except (StaleElementReferenceException, TimeoutException) as e:
            continue
            


if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--force-device-scale-factor=1")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.maximize_window()
    driver.get("http://127.0.0.1:3000")
    driver.implicitly_wait(10)
    driver.find_element(by=By.XPATH, value='//button[text()="stockholm"]').click()

    el = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH, '//div[@id="innerdock"]//button[text()="{}"]'.format(PROJECT_NAME))))
    el.click()
    # removeModifications()

    # filenames = glob.glob("./lib/actions/analysis/stock_nowater_pairs_400_*.json")
    # for filename in filenames:
    #     start_time = START_TIME
    #     minLat, minLon, maxLat, maxLon = findCorners(filename)
    #     name = filename.split("/")[-1].split(".json")[0]
    #     if exists("./" + name + ".png"):
    #         continue
    #     centerLat = (minLat + maxLat) / 2
    #     centerLon = (minLon + maxLon) / 2
    #     print(name, minLat, minLon, maxLat, maxLon, centerLat, centerLon)

    #     # Create new project 
    #     # WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH, '//button[text()="Create new Project"]')))    
    #     # driver.find_element(by=By.XPATH, value='//button[text()="Create new Project"]').click()
    #     # nameLabel = driver.find_element(by=By.XPATH, value='//label[text()="Project name"]')
    #     # driver.find_element(by=By.ID, value=nameLabel.get_attribute("for")).send_keys(name)

    #     # driver.find_element(by=By.XPATH, value='//div[contains(@class, "indicatorContainer")]').click()
    #     # driver.find_element(by=By.XPATH, value='//div[text()="y"]').click()
    #     # driver.find_element(by=By.XPATH, value='//button[text()="Create"]').click()
    #     # time.sleep(2)

    #     # Compute the most popular stop in this area 
    #     safeClick('//div[@id="sidebar"]//div[@title="Analyze"]')
    #     try:
    #         safeClick('//div[@id="PrimaryAnalysisSettings"]//button[@title="expand"]')
    #     except TimeoutException:
    #         print("do nothing")
    #     safeClick('//div[@role="tablist"]//button[@title="Custom JSON editor"]')
    #     textArea = driver.find_element(by=By.ID, value="customProfileRequest")
    #     textArea.clear()
    #     textArea.send_keys(ANALYSIS_REQUEST.format(PROJECT_ID, minLat, minLon, maxLat, maxLon, centerLat, centerLon, name))
    #     time.sleep(5)
    #     # projectLabel = driver.find_element(by=By.XPATH, value='//label[text()="Project"]')
    #     # driver.find_element(by=By.ID, value=projectLabel.get_attribute("for")).click()
    #     # driver.find_element(by=By.XPATH, value='//div[@id="{}"]//div[text()="project"]'.format(projectLabel.get_attribute("for"))).click()
    #     safeClick('//button[@title="Fetch results"]')
    #     try:
    #         WebDriverWait(driver,10).until(EC.presence_of_element_located((By.ID, 'popularStops')))    
    #     except TimeoutException:
    #         print("Skipping %s because no stops", name) # skip this region, as there are no stops in it 
    #         continue
    #     popularStops = driver.find_element(by=By.ID, value="popularStops").get_attribute("innerHTML").split("\n")

    #     # Using these stops, create modification to remove them
    #     safeClick('//div[@id="sidebar"]//div[@title="Edit Modifications"]')
    #     for stopString in popularStops:
    #         if len(stopString) > 0:
    #             removeStop(stopString)
    #     safeClick('//button[@aria-label="Show all modifications"]')

    #     safeClick('//div[@id="sidebar"]//div[@title="Test"]')
    #     # Run test with this to download the isochrone and take a screenshot 
    #     safeClick('//div[@id="PrimaryAnalysisSettings"]//button[@title="expand"]')
    #     scenarioLabel = driver.find_element(by=By.XPATH, value='//label[text()="Scenario"]')
    #     safeClick('//div[@id="{}"]'.format(scenarioLabel.get_attribute("for")))
    #     safeClick('//div[@id="{}"]//div[text()="Default"]'.format(scenarioLabel.get_attribute("for")))

    #     safeClick('//div[@role="tablist"]//button[@title="Custom JSON editor"]')
    #     for _ in range(20):
    #         driver.find_element(by=By.XPATH, value='//textarea[@id="customProfileRequest"]').send_keys(Keys.COMMAND + "a")
    #         driver.find_element(by=By.XPATH, value='//textarea[@id="customProfileRequest"]').send_keys(Keys.DELETE)
    #         driver.find_element(by=By.XPATH, value='//textarea[@id="customProfileRequest"]').send_keys(TEST_REQUEST.format(start_time, start_time+WINDOW, PROJECT_ID, centerLat, centerLon, name))
    #         start_time += WINDOW
    #         print(start_time)
    #         time.sleep(5)
    #         safeClick('//button[@title="Fetch results"]')
    #         # time.sleep(120)
    #         try:
    #             WebDriverWait(driver,120).until(EC.presence_of_element_located((By.XPATH, '//button[@title="Fetch results"]')))   
    #         except TimeoutException:
    #             time.sleep(600)
    #             WebDriverWait(driver,480).until(EC.presence_of_element_located((By.XPATH, '//button[@title="Fetch results"]')))   
    #         driver.save_screenshot("{}-{}.png".format(name, start_time))

    #     # Remove modifications
    #     safeClick('//div[@id="sidebar"]//div[@title="Edit Modifications"]')
    #     removeModifications()

    driver.quit()