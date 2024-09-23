import pandas as pd
from selenium import webdriver
from selenium.webdriver.common import options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import time

# BRAND = "mowalola"
# BRAND = "number-n-ine"
# BRAND = "rick-owens"
# BRAND = "rick-owens"
# BRAND = "alpinestars"
BRAND = "prada"


BASE_URL = f"https://www.grailed.com/designers/{BRAND}"
DATA_FILE_NAME = f"{BRAND}_data.csv"

PRODUCT_XPATH = "//div[@class='feed-item']"
DROP_DOWN_XPATH = "//*[@class='ais-SortBy-select']"
NEWEST_CSS_VALUE = "Listing_by_date_added_production"
LINKS_XPATH = '//div[@class="feed-item"]/a[@class="listing-item-link"]'

CHROME_OPTIONS = webdriver.ChromeOptions()

LOAD_MAX_TIME = 5
REFRESH_TIME = 10

RUNNING_TIME = 1

ITERATIONS = round(RUNNING_TIME/REFRESH_TIME)+1

MAX_LISTINGS = 500

def setup(options : options, url : str) -> webdriver :
    # Setup chrome driver
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Wait for 10 seconds for the page to load
    wait = WebDriverWait(driver, LOAD_MAX_TIME)

    # Return driver if it loaded else terminate
    try:
        wait.until(
            EC.visibility_of_element_located((By.XPATH, PRODUCT_XPATH))
        )
        print("Page loaded\n")
        return driver
    except TimeoutException:
        print("Timed out waiting for page to load")
        driver.quit()
        exit()

def teardown(driver : webdriver):
    driver.quit()
    print("\nClosing browser")

def write_as_csv(df : pd.DataFrame, file_name : str):
    df.to_csv(f'data/{file_name}', index=False)  

def get_product_info(driver : webdriver) -> pd.DataFrame | None:
    try:
        driver.refresh()
        time.sleep(3)
        # Get number of listings per page
        product_info = driver.find_elements(By.XPATH, PRODUCT_XPATH)
        num_products_per_page = len(product_info)

        # Sort by newest
        drop_down = Select(driver.find_element(By.XPATH, DROP_DOWN_XPATH))
        drop_down.select_by_value(NEWEST_CSS_VALUE)

        time.sleep(1)

        # Get listings from the page
        product_info = driver.find_elements(By.XPATH, PRODUCT_XPATH)

        product_info = [x.text for x in product_info]

        # Calculate number of scrolls
        num_scrolls = round(MAX_LISTINGS/num_products_per_page)+1

        # Scroll to the bottom of the page
        scroll(driver, num_scrolls)
        
        # Get listings again after scrolls
        product_info = driver.find_elements(By.XPATH, PRODUCT_XPATH)

        # Get important fields from the listings
        product_info = [x.text.split("\n")[1:6] for x in product_info]

        # Get links to the listings
        links = driver.find_elements(By.XPATH, LINKS_XPATH)
        links = [x.get_attribute('href') for x in links]

        for id,product in enumerate(product_info):
            # Remove useless fields
            for field in product:
                if "FREE SHIPPING" in field or "ago" in field or "See Similar" in field : product.remove(field)

            # Check if the product had an old price that is different from the new one
            # Convert prices to integers    
            if len(product) == 5 :
                prices = (product[-1], product[-2])
                for i in range(2) :
                    if "$" in prices[i]:
                        product[-(i+1)] = int(prices[i][1:])
            else :
                price = product[-1]
                if "$" in price:
                    product[-1] = int(price[1:])

            # Add link to the product
            product.insert(0,links[id])

        print(f"{len(product_info)} products found.")
        # Convert the list of lists to a dataframe
        df = pd.DataFrame(
            product_info, columns=["link","brand", "size", "product_name", "new_price", "old_price"]
        )
        return df
    except NoSuchElementException:
        print("No product info found")
        return None

def scroll(driver : webdriver, n : int): 
    for i in range(n) :
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.35)

# Keyword appears in product name
def filter_product_name(product_info : pd.DataFrame, keywords : list) -> pd.DataFrame:
    filtered = product_info.loc[product_info["product_name"].str.contains("|".join(keywords), case=False, na=False)]
    return filtered
# Brand name is one of the keywords
def filter_product_brand(product_info : pd.DataFrame, brands : list) -> pd.DataFrame:
    filtered = product_info.loc[product_info["brand"].isisn(brands)]
    return filtered
# Size is one of the keywords
def filter_product_size(product_info : pd.DataFrame, sizes : list) -> pd.DataFrame:
    filtered = product_info.loc[product_info["size"].isin(sizes)]
    return filtered
# Price is lower or higher than the given price
def filter_product_price(product_info : pd.DataFrame, price : list, lower : bool = True) -> pd.DataFrame:
    if lower:
        filtered = product_info.loc[product_info["new_price"] <= price]
    else:
        filtered = product_info.loc[product_info["new_price"] >= price]
    return filtered


def main():
    # Setup the WebDriver
    driver = setup(CHROME_OPTIONS, BASE_URL)

    try:
        for _ in range(ITERATIONS) :
            # Get page info
            product_info = get_product_info(driver)

            s_xs = filter_product_size(product_info, ["XS", "S"])

            write_as_csv(s_xs,DATA_FILE_NAME)
            print(f"Data updated in {DATA_FILE_NAME}")

            time.sleep(REFRESH_TIME)

    finally:
        # Clean up and close the driver
        teardown(driver)


if __name__ == "__main__":
    main()
