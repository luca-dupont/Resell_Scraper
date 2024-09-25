from flask import Blueprint, render_template, request, redirect
import grailed

main = Blueprint('main', __name__)

EMPTY_FILTER = ['']

@main.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@main.route('/grailed', methods=['GET', 'POST'])
def grailed_page():
    if request.method == 'POST':
        grailed.setup()

        brand = request.form.get('brand').lower().replace(' ','-')
        if not brand : 
            print("No brand entered")
            return render_template('grailed.html')
        
        max_listings = request.form.get('max-listings')
        max_listings = 500 if not max_listings else int(max_listings)

        sizes = [x.strip() for x in request.form.get('sizes').split(',')]
        keywords = [x.strip() for x in request.form.get('keywords').split(',')]
        specific_brand = request.form.get('brand-specification').strip()

        df = grailed.get(brand, max_listings)

        if df.empty :
            return render_template('grailed.html')

        if sizes != EMPTY_FILTER :
            df = grailed.filter_product_size(df, sizes)
        if keywords != EMPTY_FILTER :
            df = grailed.filter_product_name(df, keywords)
        if specific_brand != EMPTY_FILTER :
            df = grailed.filter_product_brand(df, specific_brand)

        num_products = len(df)
        
        print(f"{num_products} products found after filters.")

        grailed.write_as_csv(df, "grailed_data")

    return render_template('grailed.html')
