
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import time

base_url = "https://www.grailed.com/"

chrome_options = webdriver.ChromeOptions()

driver = webdriver.Chrome(options=chrome_options)    
driver.get(base_url)

time = 30

wait = WebDriverWait(driver, time)

try:
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='feed-item']")))
    print("Page loaded")
except TimeoutException:
    print("Timed out")
    driver.quit()
    exit()

print("Page loaded")
driver.quit()