from flask import Flask, render_template, jsonify
import os
import requests

app = Flask(__name__)

# Point this to the backend microservice container name over the bridge network
BACKEND_URL = os.getenv("CATALOG_API_URL", "http://bookstore-backend-service:8000")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/books/<string:book_id>', methods=['GET'])
def get_book_page(book_id):
    # Call your backend microservice API instead of querying a database directly
    response = requests.get(f"{BACKEND_URL}/api/books/{book_id}")
    if response.status_code == 200:
        book_data = response.json()
        return render_template('book-detail.html', book=book_data)
    return jsonify({"error": "Book page build failed"}), response.status_code

# Pass through helper to let your front-end JS components fetch data safely
@app.route('/books', methods=['GET'])
def list_books_proxy():
    response = requests.get(f"{BACKEND_URL}/api/books")
    return jsonify(response.json()), response.status_code

# ============================================================================================
# Frontend Proxy Route for Gemini AI Summary
# ============================================================================================
@app.route('/api/books/<string:book_id>/summary', methods=['GET'])
def frontend_get_book_summary(book_id):
    try:
        # Route the request across the internal Docker mesh to the backend container
        response = requests.get(f"{BACKEND_URL}/api/books/{book_id}/summary")
        
        # Pass the exact JSON payload and status code back to the browser
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": f"Frontend proxy communication failure: {str(e)}"}), 500
    
# ============================================================================================
# Category Page Rendering Route
# ============================================================================================
@app.route('/category/<string:category_name>', methods=['GET'])
def show_category_page(category_name):
    # Renders your local templates/category.html file cleanly
    return render_template('category.html', category_name=category_name)


# ============================================================================================
# Frontend Proxy Route for Category Book Data
# ============================================================================================
@app.route('/api/books/category/<string:category_name>', methods=['GET'])
def frontend_get_books_by_category(category_name):
    try:
        # Route the request across the internal Docker mesh to the backend API container
        response = requests.get(f"{BACKEND_URL}/api/books/category/{category_name}")
        
        # Pass the exact JSON payload and status code back to the browser JS engine
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": f"Frontend category proxy communication failure: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)