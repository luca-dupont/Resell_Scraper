from flask import Blueprint, render_template, request
import app.grailed as grailed
import pandas as pd

main = Blueprint('main', __name__)

GRAILED_PRODUCT_FILE_NAME = "grailed_product_data"
GRAILED_SPECIFICS_FILE_NAME = "grailed_specific_data"

INVALID_BRAND_MESSAGE = '<p style="color:red;">Please enter a brand</p>'
INVALID_NUM_LISTINGS_MESSAGE = '<p style="color:red;">Please enter a valid number of listings</p>'

EMPTY_FILTER = ['']

@main.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@main.route('/grailed', methods=['GET', 'POST'])
def grailed_page():
    message = ''
    if request.method == 'POST':
        brand = request.form.get('brand').lower().replace(' ','-')
        if not brand : 
            print("No brand entered")
            message = INVALID_BRAND_MESSAGE
            return render_template('grailed.html', message=message)
        
        max_listings = request.form.get('max-listings')
        if not max_listings :
            max_listings = 500
        try :
            max_listings = int(max_listings)
        except :
            message = INVALID_NUM_LISTINGS_MESSAGE
            return render_template('grailed.html', message=message)

        sizes = [x.strip() for x in request.form.get('sizes').split(',')]
        keywords = [x.strip() for x in request.form.get('keywords').split(',')]
        specific_brand = request.form.get('brand-specification').strip()

        products = grailed.get(brand, max_listings)

        if products.empty :
            message = '<p style="color:red;">Make sure the brand is spelled correctly</p>'
            return render_template('grailed.html', message=message)

        if sizes != EMPTY_FILTER :
            products = grailed.filter_product_size(products, sizes)
        if keywords != EMPTY_FILTER :
            products = grailed.filter_product_name(products, keywords)
        if specific_brand != '' :
            products = grailed.filter_product_brand(products, specific_brand)

        num_products = len(products)

        if num_products == 0 :
            message = '<p style="color:red;">No products found for these filters</p>'
            return render_template('grailed.html', message=message)
        
        print(f"{num_products} products found after filters.")

        message = f'<p style="color:green;">{num_products} products found and saved to {GRAILED_PRODUCT_FILE_NAME}.csv</p>'

        specifics = grailed.get_specifics(products["link"].tolist())

        grailed.write_as_csv(products, GRAILED_PRODUCT_FILE_NAME)
        grailed.write_as_csv(specifics, GRAILED_SPECIFICS_FILE_NAME)

    return render_template('grailed.html', message=message)
