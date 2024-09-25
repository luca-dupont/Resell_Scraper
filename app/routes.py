from flask import Blueprint, render_template, request, redirect
import grailed

main = Blueprint('main', __name__)

GRAILED_FILE_NAME = "grailed_data"

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
            message = '<p style="color:red;">Please enter a brand</p>'
            return render_template('grailed.html', message=message)
        
        max_listings = request.form.get('max-listings')
        if not max_listings :
            max_listings = 500
        try :
            max_listings = int(max_listings)
        except :
            message = '<p style="color:red;">Please enter a valid number of listings</p>'
            return render_template('grailed.html', message=message)

        sizes = [x.strip() for x in request.form.get('sizes').split(',')]
        keywords = [x.strip() for x in request.form.get('keywords').split(',')]
        specific_brand = request.form.get('brand-specification').strip()

        df = grailed.get(brand, max_listings)

        if df.empty :
            message = '<p style="color:red;">Make sure the brand is spelled correctly</p>'
            return render_template('grailed.html', message=message)

        if sizes != EMPTY_FILTER :
            df = grailed.filter_product_size(df, sizes)
        if keywords != EMPTY_FILTER :
            df = grailed.filter_product_name(df, keywords)
        if specific_brand != '' :
            df = grailed.filter_product_brand(df, specific_brand)

        num_products = len(df)

        if num_products == 0 :
            message = '<p style="color:red;">No products found for these filters</p>'
            return render_template('grailed.html', message=message)
        
        print(f"{num_products} products found after filters.")

        message = f'<p style="color:green;">{num_products} products found and saved to {GRAILED_FILE_NAME}.csv</p>'
        grailed.write_as_csv(df, GRAILED_FILE_NAME)

    return render_template('grailed.html', message=message)
