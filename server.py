from threading import Thread
from flask import Flask, render_template, request, jsonify
from googlesearch import search
import asyncio
from fuzzywuzzy import fuzz
from backend.webScraper import WebCrawler
from flask_cors import CORS
from flask_socketio import SocketIO
from gevent import monkey

monkey.patch_all()
app = Flask(__name__)
CORS(app, origins="*")
socketio = SocketIO(app, async_mode='gevent')

# Variable to store product data globally
global_products_data = []

def fuzzy_match(user_input, text):
    return fuzz.partial_ratio(' '.join(user_input), text)

async def main(query):
    setFlag = False
    products_data = []

    for url in search(' '.join(query), tld="co.in", num=10, stop=12, pause=0.1):
        print(url)
        if fuzzy_match(query, url) > 70:
            product_data = await WebCrawler.process_url(url, setFlag, query, socketio)
            products_data.append(product_data)
            # socketio.emit('product_data', {"status": "success", "products": [product_data]})
            
    # Emit all found product data at once
    if products_data:
        socketio.emit('product_data', {"status": "success", "products": products_data})


def run_scraping_task(query):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main(query))
    finally:
        loop.close()

@app.route('/search', methods=['POST'])
def searchItem():
    user_input = request.form['productName']
    print("User input:", user_input)

    query = user_input.split(' ')

    socketio.start_background_task(target=run_scraping_task, query=query)

    return jsonify({"status": "success", "message": "Scraping task initiated."})

@app.route('/fetchData')
def fetchData():
    global global_products_data
    return jsonify({"status": "success", "products": global_products_data})

@app.route('/')
def mockup():
    return render_template('/mockup.html')

if __name__ == '__main__':
    socketio.run(app, port=5000, debug=True)