import base64

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_pymongo import PyMongo
import uuid
import jwt
import datetime
import random

app = Flask(__name__)
CORS(app, origins="http://localhost:*", supports_credentials=True)
app.config["MONGO_URI"] = "mongodb://localhost:27017/test_app"
SECRET_KEY = "your_secret_key_here"

mongo = PyMongo(app)


@app.route('/image', methods=['GET'])
def img():
    userId = '2f3c5b31-0bb9-4c50-a09b-e961baeeccca'
    post = mongo.db.post
    img_date = post.find_one({'user_id': userId})
    print(img_date)
    if img_date:
        image = img_date['img']
        image_base64 = base64.b64encode(image).decode('utf-8')
        return jsonify({"image": image_base64})
    return jsonify('none')


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
            token = jwt.encode(
                {"user_id": user['user_id'], "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)},
                SECRET_KEY, algorithm="HS256", )
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


@app.route('/home/process', methods=['GET'])
def process():
    a = [random.random() for _ in range(6)]
    for i in range(24):
        a.append(-1)
    return jsonify(a)


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


@app.route('/question', methods=['POST'])
def question():
    data = request.get_json()
    question = data.get('qa')
    userId = data.get('userId')
    learn = [question['0'], question['1'], question['2'], question['3'], question['4'], question['5']]
    user = mongo.db.users
    update_date = {
        '$set': {
            'question': learn
        }
    }
    user.update_one({'userId': userId}, update_date)
    return jsonify('login success')


@app.route('/forum/post', methods=['POST'])
def post():
    try:
        token = request.headers.get('Authorization').split("Bearer ")[1]
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = data["user_id"]
        print(user_id)
        post = mongo.db.post
        date = request.get_json()
        title = date.get('title')
        tag = date.get('tag')
        passage = date.get('passage')
        img = date.get('img')
        print(img)
        image_data = None
        if img is not None:
            image_data = base64.b64decode(img)
        document = {'user_id': user_id, 'title': title, 'tag': tag, 'passage': passage}
        if image_data:
            document['img'] = image_data
        post.insert_one(document)
        print(tag)
        return jsonify('success')
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired, please login again.'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/Person', methods=['GET'])
def person():
    try:
        token = request.headers.get('Authorization').split("Bearer ")[1]
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = data["user_id"]
        print('user_id', user_id)
        if user_id:
            users = mongo.db.users
            quire = {'user_id': user_id}
            user = users.find_one(quire)
            if user:
                return jsonify(
                    {'name': user['name'], 'account': user['account'], 'fans': user['fans'], 'post': user['posts'],
                     'follows': user['follows']})
        return jsonify({'message': 'User not found'})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired, please login again.'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
