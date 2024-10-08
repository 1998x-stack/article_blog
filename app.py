import os
import json
import logging
import sqlite3
from typing import List, Tuple, Union
from flask import Flask, render_template, request, jsonify

# Configuration Constants
DB_PATH = 'blog.db'
ARTICLES_PER_PAGE = 6

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

def initialize_database(db_path: str = DB_PATH) -> None:
    try:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL
                )
            ''')
            logging.info("Database initialized successfully.")
    except sqlite3.Error as error:
        logging.error(f"Error while initializing the database: {error}")

# Initialize the SQLite database
initialize_database()

def get_articles_from_db(db_path: str, limit: int, offset: int) -> List[Tuple[int, str, str, str]]:
    try:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('SELECT id, title, content, tags FROM articles LIMIT ? OFFSET ?', (limit, offset))
            articles = cursor.fetchall()
            return articles
    except sqlite3.Error as error:
        logging.error(f"Error while fetching articles: {error}")
        return []

def get_article_by_id(db_path: str, article_id: int) -> Union[Tuple[int, str, str, str], None]:
    try:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('SELECT id, title, content, tags FROM articles WHERE id = ?', (article_id,))
            article = cursor.fetchone()
            return article
    except sqlite3.Error as error:
        logging.error(f"Error while fetching article by id: {error}")
        return None

def insert_article_to_db(db_path: str, title: str, content: str, tags: str) -> Union[bool, str]:
    try:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('INSERT INTO articles (title, content, tags) VALUES (?, ?, ?)', (title, content, tags))
            connection.commit()
            return True
    except sqlite3.Error as error:
        logging.error(f"Error inserting article: {error}")
        return str(error)

@app.route('/')
def index():
    view_type = request.args.get('view', 'grid')
    try:
        page = max(int(request.args.get('page', 1)), 1)
    except ValueError:
        page = 1
    
    offset = (page - 1) * ARTICLES_PER_PAGE
    articles = get_articles_from_db(DB_PATH, ARTICLES_PER_PAGE, offset)
    
    return render_template('index.html', articles=articles, view_type=view_type, page=page)

@app.route('/article/<int:article_id>')
def article(article_id):
    article = get_article_by_id(DB_PATH, article_id)
    if article is None:
        return "Article not found", 404
    return render_template('article.html', article=article)

@app.route('/import_json', methods=['POST'])
def import_json():
    if ('file' not in request.files or request.files['file'].filename == '') and not request.data:
        return jsonify({"error": "No file part in the request or no selected file, or empty data"}), 400
    
    articles_data = None

    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        if not file.filename.endswith('.json'):
            return jsonify({"error": "Invalid file type. Please upload a JSON file."}), 400
        try:
            file_content = file.read().decode('utf-8')
            articles_data = json.loads(file_content)
        except (json.JSONDecodeError, ValueError) as error:
            return jsonify({"error": f"Invalid JSON format: {error}"}), 400
    else:
        try:
            articles_data = json.loads(request.data.decode('utf-8'))
        except (json.JSONDecodeError, ValueError) as error:
            return jsonify({"error": f"Invalid JSON format: {error}"}), 400

    if not isinstance(articles_data, list):
        return jsonify({"error": "JSON file content must be a list of articles."}), 400

    for article in articles_data:
        title = article.get('title')
        content = article.get('content')
        tags = article.get('tags')

        if not title or not content or not tags:
            return jsonify({"error": "Missing fields in some articles."}), 400

        result = insert_article_to_db(DB_PATH, title, content, tags)
        if result is not True:
            return jsonify({"error": f"Failed to insert article: {result}"}), 500

    return jsonify({"success": "Articles imported successfully!"}), 201

if __name__ == '__main__':
    app.run(debug=True)