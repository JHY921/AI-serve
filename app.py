from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
import uuid

app = Flask(__name__)
CORS(app)
app.config["MONGO_URI"] = "mongodb://localhost:27017/test_app"
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
            return jsonify({'message': True, 'user_id': user['user_id']})
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
    print(account, password, user_id)
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
        }
    }
    users = mongo.db.users
    print(user_id)
    print(name)
    result = users.update_one({'user_id': user_id}, update_data)
    return jsonify('success')


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
