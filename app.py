from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_pymongo import PyMongo
import uuid
import jwt
import datetime

app = Flask(__name__)
CORS(app,origins="http://localhost:*", supports_credentials=True)
app.config["MONGO_URI"] = "mongodb://localhost:27017/test_app"
SECRET_KEY = "your_secret_key_here"

mongo = PyMongo(app)


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    account = data.get('account')
    password = data.get('password')
    users = mongo.db.users
    quire = {'account': account}
    user = users.find_one(quire)
    if user:
        check_password = user['password']
        if check_password == password:
            # session['id'] = user['user_id']
            # print(session.get('id'))
            token = jwt.encode({"user_id": user['user_id'], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours = 1)}, SECRET_KEY, algorithm="HS256", )
            return jsonify({'message': True, 'user_id': user['user_id'], 'token': token})
        return jsonify({'message': False})
    else:
        return jsonify({'message': False})


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    account = data.get('tel')
    password = data.get('password')
    user_id = str(uuid.uuid4())
    user = mongo.db.users
    new_users = {"account": account, 'password': password, 'user_id': user_id}
    user.insert_one(new_users)
    return jsonify(user_id)


@app.route('/userinfo', methods=['POST'])
def userinfo():
    data = request.get_json()
    name = data.get('name')
    birth = data.get('birth')
    degree = data.get('degree')
    sex = data.get('sex')
    user_id = data.get('id')
    update_data = {
        '$set': {
            'name': name,
            'birth': birth,
            'degree': degree,
            'sex': sex,
            'fans': 0,
            'follows': 0,
            'posts': 0,
        }
    }
    users = mongo.db.users
    result = users.update_one({'user_id': user_id}, update_data)
    return jsonify('success')


@app.route('/Person', methods=['GET'])
def person():
    # user_id = session.get('id')
    token = request.headers.get('Authorization').split("Bearer ")[1]
    data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user_id = data["user_id"]
    print('user_id', user_id)
    if user_id:
        users = mongo.db.users
        quire = {'user_id': user_id}
        user = users.find_one(quire)
        if user:
            return jsonify({'fans': user['fans'], 'post': user['posts'], 'follows': user['follows']})
    return jsonify({'message': 'User not found'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
