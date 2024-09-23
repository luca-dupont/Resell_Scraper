import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import time

base_url = "https://www.farfetch.com/ca/shopping/men/acne-studios/items.aspx"

product_xpath = '//div[@data-testid="product"]'
sort_by_xpath = '//div[@data-testid="sort-by-button"]'

chrome_options = webdriver.ChromeOptions()

MAX_LISTINGS = 1000

def setup(options, url):
    # Setup chrome driver
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Wait for 10 seconds for the page to load
    time = 10
    wait = WebDriverWait(driver, time)

    # Return driver if it loaded else terminate
    try:
        wait.until(
            EC.visibility_of_element_located((By.XPATH, product_xpath))
        )
        print("Page loaded\n")
        return driver
    except TimeoutException:
        print("Timed out waiting for page to load")
        driver.quit()
        exit()

def teardown(driver):
    driver.quit()
    print("\nClosing browser")

def write_as_csv(df, file_name):
    df.to_csv(f'data/{file_name}.csv', index=False)  

def get_product_info(driver):
    try:
        # Get number of listings pr page
        product_info = driver.find_elements(By.XPATH, product_xpath)
        print([x.text for x in product_info])
        num_products_per_page = len(product_info)

        # Sort by newest
        drop_down_menu = driver.find_element(By.XPATH, sort_by_xpath)
        drop_down_menu.click()

        time.sleep(1)

        # Get listings from the page
        product_info = driver.find_elements(By.XPATH, product_xpath)

        product_info = [x.text for x in product_info]

        # Calculate number of scrolls
        num_scrolls = round(MAX_LISTINGS/num_products_per_page)+1

        # Scroll to the bottom of the page
        scroll(driver, num_scrolls)
        
        # Get listings again after scrolls
        product_info = driver.find_elements(By.XPATH, product_xpath)

        # Get important fields from the listings
        product_info = [x.text.split("\n")[1:6] for x in product_info]

        # Get links to the listings
        links = driver.find_elements(By.XPATH, product_xpath)
        links = [x.get_attribute('href') for x in links]

        print(len(product_info))

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

        # Convert the list of lists to a dataframe
        df = pd.DataFrame(
            product_info, columns=["link","brand", "size", "product_name", "new_price", "old_price"]
        )
        return df
    except NoSuchElementException:
        print("No product info found")
        return None

def scroll(driver, n) : 
    for i in range(n) :
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.3)


def main():
    # Setup the WebDriver
    driver = setup(chrome_options, base_url)

    try:
        # Get page info
        product_info = get_product_info(driver)
        product_info.sort_values(by="new_price", inplace=True)

        # gats = product_info.loc[
        #     product_info["product_name"].str.contains(
        #         "GAT|German Army Trainer", case=False, na=False
        #     )
        # ]
        # Get rows with sizes of 8.5,9, or 9.5
        # sizes = gats.loc[gats["size"].str.contains("8.5|9|9.5", case=False, na=False)]

        write_as_csv(product_info, "farfetch_data")

    finally:
        # Clean up and close the driver
        teardown(driver)


if __name__ == "__main__":
    main()
