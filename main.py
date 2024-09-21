import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import time

base_url = "https://www.grailed.com/designers/maison-margiela"

chrome_options = webdriver.ChromeOptions()


def setup(options, url):
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    time = 30
    wait = WebDriverWait(driver, time)

    try:
        wait.until(
            EC.visibility_of_element_located((By.XPATH, "//div[@class='feed-item']"))
        )
        print("Page loaded")
        return driver
    except TimeoutException:
        print("Timed out")
        driver.quit()
        exit()


def teardown(driver):
    driver.quit()
    print("Closing browser")


def get_product_info(driver):
    try:
        product_info = driver.find_elements(By.XPATH, "//div[@class='feed-item']")
        product_info = [x.text for x in product_info]
    
        product_info = [x.split("\n")[1:5] for x in product_info]
        for product in product_info:
            for field in product:
                if "FREE SHIPPING" in field:
                    product.remove(field)
                if "ago" in field:
                    product.remove(field)
                if "See Similar" in field:
                    product.remove(field)
                    
        df = pd.DataFrame(
            product_info, columns=["brand", "size", "product_name", "price"]
        )
        return df
    except NoSuchElementException:
        print("No product info found")
        return None


def main():
    # Setup the WebDriver
    driver = setup(chrome_options, base_url)

    try:
        # for _ in range(10):
        product_info = get_product_info(driver)
        print(product_info)

    finally:
        # Clean up and close the driver
        teardown(driver)


if __name__ == "__main__":
    main()
