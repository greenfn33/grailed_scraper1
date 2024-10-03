import os
import webbrowser
from flask import Flask, request, render_template, send_file
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)

# parser
def fetch_page(url):
    try:
        headers = {
            "User -Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        return None

# Function to scrape products from Grailed
def scrape_grailed_products(query, limit, page=1):
    base_url = 'https://www.grailed.com/'
    search_url = f'{base_url}search?q={query}&page={page}'
    soup = fetch_page(search_url)

    if soup is None:
        print(f"Failed to fetch page: {search_url}")
        return []

    products = []
    product_cards = soup.find_all('div', class_='feed-item', limit=limit)

    for product in product_cards:
        title_tag = product.find('div', class_='listing-card__title')
        link_tag = product.find('a', class_='listing-card__link')
        price_tag = product.find('div', class_='listing-card__price')

        if title_tag and link_tag and price_tag:
            title = title_tag.get_text(strip=True)
            link = 'https://www.grailed.com' + link_tag['href']  # *PROBLEM* chduijbvfiubcfbivbovbfiobvfiol
            price = price_tag.get_text(strip=True)

            # Attempt to find sizes if available (not working)
            size_tag = product.find('div', class_='listing-card__size')  # Adjust class name based on actual HTML
            size = size_tag.get_text(strip=True) if size_tag else "N/A"

            products.append({
                'title': title,
                'link': link,
                'price': price,
                'size': size  # Add size to product details (not working)
            })

    # Check if there's a next page (not working)
    next_page_link = soup.find('a', class_='pagination__next')
    if next_page_link:
        page += 1
        products.extend(scrape_grailed_products(query, limit, page))

    return products

# Function to save the products into a csv file
def save_to_csv(products, filename):
    file_path = os.path.join(os.getcwd(), filename)
    df = pd.DataFrame(products)
    df.to_csv(file_path, index=False)
    return file_path  # Return the full file path

# Flask route for home page (search input)
@app.route('/')
def index():
    return '''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <title>Grailed Product Search</title>
        <style>
            body {
                background-color: #f8f9fa;
                padding: 30px;
            }
            h1 {
                color: #343a40;
                text-align: center;
                margin-bottom: 30px;
            }
            .form-container {
                background-color: #ffffff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            .btn-pretty {
                background: linear-gradient(45deg, #6a11cb, #2575fc);
                border: none;
                color: white;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 50px;
                text-transform: uppercase;
                cursor: pointer;
                transition: background 0.3s ease;
            }
            .btn-pretty:hover {
                background: linear-gradient(45deg, #2575fc, #6a11cb);
            }
            .result {
                margin-top: 30px;
            }
            a {
                color: #343a40;
                text-decoration: none;
                font-weight: bold;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container form-container">
            <h1>Search Grailed</h1>
            <form action="/search" method="post">
                < div class="form-group">
                    <label for="query">Enter search term:</label>
                    <input type="text" class="form-control" id="query" name="query" required>
                </div>
                <div class="form-group">
                    <label for="limit">Number of results:</label>
                    <input type="number" class="form-control" id="limit" name="limit" min="1" value="5" required>
                </div>
                <button type="submit" class="btn btn-pretty btn-block">Search</button>
            </form>
        </div>
    </body>
    </html>
    '''

# Flask route to perform the search and scrape
@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    limit = int(request.form['limit'])  # Get the number of results wanted
    products = scrape_grailed_products(query, limit)

    if products:
        output_file = f"{query}_grailed_products.csv"
        file_path = save_to_csv(products, output_file)  # Save CSV and get file path

        return f'''
        <div class="container result">
            <h2>Search results for "{query}"</h2>
            <table class="table table-bordered">
                <thead class="thead-light">
                    <tr>
                        <th>Product</th>
                        <th>Price</th>
                        <th>Link</th>
                        <th>Size</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(f"<tr><td>{p['title']}</td><td>{p['price']}</td><td><a href='{p['link']}' target='_blank'>View Product</a></td><td>{p['size']}</td></tr>" for p in products)}
                </tbody>
            </table>
            <p><a href="/download/{output_file}" class="btn btn-pretty">Download CSV</a></p>
        </div>
        '''
    else:
        return f"<h2>No products found for '{query}'</h2>"

# Flask route to download the CSV file
@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(os.getcwd(), filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return f"<h2>File {filename} not found.</h2>"

# Run the Flask app
if __name__ == '__main__':
    webbrowser.open("http://127.0.0.1:5000/")
    app.run(debug=True)