from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson.objectid import ObjectId
from google import genai
import os
import sys

app = Flask(__name__)

# Fallback string matches the internal docker-compose service name
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb-backend:27017/bookstore")
client = MongoClient(MONGO_URI)
db = client['bookstore']

# CRITICAL INITIALIZATION ERROR GATEWAY (Project 2 Requirement)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("CRITICAL INITIALIZATION ERROR: GEMINI_API_KEY environment variable is completely missing!", file=sys.stderr)
    sys.exit(1) # Drop exit status code 1 for the CI/CD pipeline gate

ai_client = genai.Client(api_key=GEMINI_API_KEY)

@app.route('/api/books', methods=['GET'])
def get_all_books():
    try:
        books = list(db['books'].find())
        for book in books:
            book['_id'] = str(book['_id'])
        return jsonify(books), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/books/<string:book_id>', methods=['GET'])
def get_single_book(book_id):
    try:
        book = db['books'].find_one({'_id': ObjectId(book_id)})
        if book:
            book['_id'] = str(book['_id'])
            return jsonify(book), 200
        return jsonify({"error": "Book not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/books/<string:book_id>/summary', methods=['GET'])
def get_book_summary(book_id):
    try:
        book = db['books'].find_one({'_id': ObjectId(book_id)})
        if not book:
            return jsonify({"error": "Target book record missing"}), 404
        
        prompt = f"Summarize {book.get('title')} by {book.get('author')} concisely."
        response = ai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        
        return jsonify({"book_id": book_id, "ai_summary": response.text}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/books/category/<string:category_name>', methods=['GET'])
def get_books_by_category(category_name):
    try:
        books_collection = db['books']
        # Query MongoDB for documents matching the exact category parameter string
        books_cursor = books_collection.find({"category": category_name})
        books_list = []
        for book in books_cursor:
            book['_id'] = str(book['_id']) 
            books_list.append(book)
        return jsonify(books_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)