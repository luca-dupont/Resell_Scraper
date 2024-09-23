import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import time

base_url = "https://www.grailed.com/designers/chrome-hearts"

chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--headless=new")


def setup(options, url):
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    time = 10
    wait = WebDriverWait(driver, time)

    try:
        wait.until(
            EC.visibility_of_element_located((By.XPATH, "//div[@class='feed-item']"))
        )
        return driver
    except TimeoutException:
        print("Timed out waiting for page to load")
        driver.quit()
        exit()


def teardown(driver):
    driver.quit()
    print("\nClosing browser")


def get_product_info(driver):
    try:
        product_info = driver.find_elements(By.XPATH, "//div[@class='feed-item']")
        product_info = [x.text for x in product_info]

        product_info = [x.split("\n")[1:6] for x in product_info]
        for product in product_info:
            for field in product:
                if "FREE SHIPPING" in field or "ago" in field or "See Similar" in field:
                    product.remove(field)
            if len(product) == 5 :
                prices = (product[-2], product[-1])
                for i in range(2) :
                    if "$" in prices[i]:
                        product[-(i+1)] = int(prices[i][1:])
            else :
                price = product[-1]
                if "$" in price:
                    product[-1] = int(price[1:])

        df = pd.DataFrame(
            product_info, columns=["brand", "size", "product_name", "new_price", "old_price"]
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
        product_info.sort_values(by="new_price", inplace=True)

        # gats = product_info.loc[
        #     product_info["product_name"].str.contains(
        #         "GAT|German Army Trainer", case=False, na=False
        #     )
        # ]
        # Get rows with sizes of 8.5,9, or 9.5
        # sizes = gats.loc[gats["size"].str.contains("8.5|9|9.5", case=False, na=False)]

        print(product_info)

    finally:
        # Clean up and close the driver
        teardown(driver)


if __name__ == "__main__":
    main()
