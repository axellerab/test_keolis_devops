# INFO IMPORTANTES : "https://www.qatouch.com/blog/how-to-run-selenium-webdriver-with-docker/"

# 1.IMPORT PACKAGES
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import urllib.request
import os
import time
from datetime import datetime
from datetime import timedelta
import argparse
import csv_transfo
import blobtools

# 2.DECLARE VARIABLES
# 2.1 parameters
parser = argparse.ArgumentParser()
parser.add_argument("--sa", help="storage account.", type=str)
parser.add_argument("--sk", help="storage key.", type=str)
parser.add_argument("--cs", help="connect string to gen2.", type=str)
parser.add_argument("--url", help="url meteo merra forecast.", type=str)
parser.add_argument("--lat", help="latitude.", type=str)
parser.add_argument("--lon", help="longitude.", type=str)
parser.add_argument("--fl", help="forecast length.", type=str)
args = parser.parse_args()
# 2.2 variables selenium
meteoforecasturl = args.url
lat = args.lat
lon = args.lon
forecastlength = int(args.fl)
datjour = datetime.today().strftime(format='%Y-%m-%d')
datfin = (datetime.today() + timedelta(days=forecastlength)).strftime(format='%Y-%m-%d')
# 2.3 variables blob
pattern = 'GFS'
storage_account = args.sa
storage_key = args.sk
connect_str_gen2 = args.cs
container_name = "meteosodamerraforecast"


# 3.DECLARE FUNCTIONS
def mount_firefox_image():
    cmd1 = "sudo docker pull selenium/standalone-firefox"
    cmd11 = "sudo docker kill $(sudo docker ps -q)"
    cmd2 = "sudo docker run -d -p 4444:4444 selenium/standalone-firefox"

    os.system(cmd1)
    os.system(cmd11)
    os.system(cmd2)
    time.sleep(5)

def create_driver(url=meteoforecasturl):
    driver = webdriver.Remote(
        command_executor='http://127.0.0.1:4444/wd/hub',
        desired_capabilities=DesiredCapabilities.FIREFOX)
    driver.get(url)

    while "GFS forecasts" not in driver.title:
        time.sleep(10)
        driver.get(url)

    return driver

def fill_process_form(driver, lat, lon, datjour, datfin):
    elem = driver.find_element_by_id("latId")
    elem.clear()
    elem.send_keys(lat)
    elem = driver.find_element_by_id("lonId")
    elem.clear()
    elem.send_keys(lon)
    elem = driver.find_element_by_id("dateBegin")
    elem.clear()
    elem.send_keys(datjour)
    elem = driver.find_element_by_id("dateEnd")
    elem.clear()
    elem.send_keys(datfin)
    process_button = driver.find_element_by_id("ext-gen70")
    process_button.click()
    dl_button = driver.find_element_by_id("responseLink")
    while dl_button.get_attribute('href') == '':
        time.sleep(1)
    link = dl_button.get_attribute('href')
    driver.close()
    return link

def download_file(link):
    file_name = link.split('/')[-1]
    dl_path = os.getcwd() + '/' + file_name
    urllib.request.urlretrieve(link, dl_path)
    return dl_path, file_name


# RUN
mount_firefox_image()
link = fill_process_form(create_driver(url=meteoforecasturl), lat, lon, datjour, datfin)
local_path, file_name = download_file(link)

# file_path_full = csv_transfo.detect_full_path(local_path, pattern)
str_to_write = csv_transfo.lecture(local_path)
csv_transfo.transform_merra_file(local_path,str_to_write)

blob_service_client = blobtools.connect_blob(connect_str=connect_str_gen2)
blobtools.create_or_update_container(blob_service_client, container_name)
blobtools.upload_file_to_blob(blob_service_client, local_path, container_name, file_name)

