import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException
import time
from typing import List


PRODUCT_XPATH = "//div[@class='feed-item']"
DROP_DOWN_XPATH = "//*[@class='ais-SortBy-select']"
NEWEST_CSS_VALUE = "Listing_by_date_added_production"
LINKS_XPATH = '//div[@class="feed-item"]/a[@class="listing-item-link"]'
AUTHENTICATED_XPATH = "//*[contains(text(), 'Authenticated')]"

#! NEED TO FIX THIS todo!
RATING_XPATH = "//*[@class='Text Subhead-module__subhead___Q54qe SellerScore-module__rating___oL8oF']"
NUM_REVIEWS_XPATH = "//*[@class='Text Subhead-module__subhead___Q54qe SellerScore-module__reviews___RHfbY']"
SELLER_INFO_XPATH = "//*[@class='SellerScore_sellerScore__ksdKN SellerDetails_sellerScore__oJJ1t']"
SELLER_NAME_XPATH = "//*[@class='Headline-module__headline___47Ed7 Text Info-module__username___5XoXR']"
TRANSACTION_COUNT_XPATH = "//*[@class='Text Callout-module__callout___Zy1Od Info-module__transactions___uWlJ+']"

CHROME_OPTIONS = webdriver.ChromeOptions()

driver = None

def setup_head() :
    global driver

    try :
        # Start Chrome
        driver = webdriver.Chrome(CHROME_OPTIONS)
        print("\nChrome started\n")
    except :
        print("Error: Could not start Chrome")
        exit()

def setup_headless() :
    global driver

    hl_options = webdriver.ChromeOptions()
    hl_options.add_argument("--headless=new")

    try :
        # Start Chrome
        driver = webdriver.Chrome(options=hl_options)
        print("\nChrome started\n")
    except :
        print("Error: Could not start Chrome")
        exit()

def teardown(driver : webdriver):
    driver.quit()
    print("\nClosing browser\n")

def write_as_csv(df : pd.DataFrame, file_name : str):
    df.to_csv(f'data/{file_name}.csv', index=False)  

def get_product_info(driver : webdriver, max_listings : int) -> pd.DataFrame | None:
    try:
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
        num_scrolls = round(max_listings/num_products_per_page)+2

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
            for i,field in enumerate(product):
                product_info[id][i] = field.lower()
                field = field.lower()
                if "free shipping" in field or "ago" in field or "similar" in field : 
                    product_info[id].remove(field)

            product = product_info[id]
            # Check if the product had an old price that is different from the new one
            # Convert prices to integers    
            if len(product) == 5 :
                prices = (product[-1], product[-2])
                for i in range(2) :
                    if "$" in prices[i]:
                        product_info[id][-(i+1)] = int(prices[i][1:])
            else :
                price = product[-1]
                if "$" in price:
                    product_info[id][-1] = int(price[1:])
                product_info[id].append(None)

            # Add link to the product
            product_info[id].insert(0,links[id])

        # Convert the list of lists to a dataframe
        df = pd.DataFrame(
            product_info, columns=["link","brand", "size", "product_name", "new_price", "old_price"]
        )

        if len(df) > max_listings :
            df = df.head(max_listings)

        print(f"{len(df)} products found before filters.")

        return df
    except NoSuchElementException:
        print("No product info found")
        return pd.DataFrame()

def get_product_specifics(driver : webdriver, product_url : str) -> pd.DataFrame:
    try :
        driver.get(product_url)

        driver.timeouts.implicit_wait = 0
        authenticated = driver.find_elements(By.XPATH, AUTHENTICATED_XPATH) is not None
        driver.timeouts.implicit_wait = 3

        review_link = driver.find_element(By.XPATH, SELLER_INFO_XPATH).get_attribute('href')
        reviews_url = f"https://www.grailed.com{review_link}"

        driver.get(reviews_url)

        rating = driver.find_element(By.XPATH, RATING_XPATH).text
        num_reviews = driver.find_element(By.XPATH, NUM_REVIEWS_XPATH).text
        seller = driver.find_element(By.XPATH, SELLER_NAME_XPATH).text
        transaction_count = driver.find_element(By.XPATH, TRANSACTION_COUNT_XPATH).text

        product_specifics = pd.DataFrame(
            {
                "link" : [product_url],
                "authenticated" : [authenticated],
                "rating" : [rating],
                "num_reviews" : [num_reviews],
                "transaction_count" : [transaction_count],
                "seller" : [seller]
            }
        )
        return product_specifics
        
    except Exception as e:
        print(f"Could not get product specifics for {product_url}")
        return pd.DataFrame()

def scroll(driver : webdriver, n : int): 
    for i in range(n) :
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.35)

# Keyword appears in product name
def filter_product_name(product_info : pd.DataFrame, keywords : List[str]) -> pd.DataFrame:
    keywords = [x.lower() for x in keywords]
    filtered = product_info.loc[product_info["product_name"].str.contains("|".join(keywords), case=False, na=False)]
    return filtered
# Brand name is one of the keywords
def filter_product_brand(product_info : pd.DataFrame, brand : str) -> pd.DataFrame:
    brand = brand.lower()

    filtered = product_info.loc[product_info["brand"] == brand]
    return filtered
# Size is one of the keywords
def filter_product_size(product_info : pd.DataFrame, sizes : List[str]) -> pd.DataFrame:
    sizes = [x.lower() for x in sizes]
    filtered = product_info.loc[product_info["size"].isin(sizes)]
    return filtered
# Price is lower or higher than the given price
def filter_product_price(product_info : pd.DataFrame, price : int, lower : bool = True) -> pd.DataFrame:
    if lower:
        filtered = product_info.loc[product_info["new_price"] <= price]
    else:
        filtered = product_info.loc[product_info["new_price"] >= price]
    return filtered

def get(brand : str, max_listings : int) -> pd.DataFrame:
    global driver
    setup_head()

    url = f"https://www.grailed.com/designers/{brand}"

    try:
        driver.set_window_position(10000, 10000)
        driver.get(url)

        time.sleep(2)

        # Get page info
        product_info = get_product_info(driver, max_listings)
        return product_info
    finally:
        # Clean up and close the driver
        teardown(driver)

def get_specifics(urls : List[str]) -> pd.DataFrame:
    global driver
    setup_headless()

    specifics = pd.DataFrame(columns=['link','authenticated','rating','num_reviews','transaction_count','seller'])

    try : 
        for url in urls :
            specifics = pd.concat([specifics, get_product_specifics(driver, url)], ignore_index=True)  
    finally : 
        teardown(driver)

    return specifics
