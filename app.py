from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
import uuid

app = Flask(__name__)
CORS(app)
app.config["MONGO_URI"] = "mongodb://localhost:27017/test_app"
mongo = PyMongo(app)