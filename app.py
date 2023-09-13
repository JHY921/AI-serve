import base64
import os
from flask import Flask, request, jsonify, session, send_from_directory, send_file
from flask_cors import CORS
from flask_pymongo import PyMongo
import uuid
import jwt
import datetime
import random
import OCR
from decimal import Decimal
from bson.objectid import ObjectId
import SparkApi

appid = "0f853b71"  # 填写控制台中获取的 APPID 信息
api_secret = "MmZjZjFhMjEyZDQ5NDBhMDY4MmNjN2Uz"  # 填写控制台中获取的 APISecret 信息
api_key = "2578758349fb1df97b02bbcc9f896d53"  # 填写控制台中获取的 APIKey 信息

# 用于配置大模型版本，默认“general/generalv2”
domain = "general"  # v1.5版本
# domain = "generalv2"    # v2.0版本
# 云端环境的服务地址
Spark_url = "ws://spark-api.xf-yun.com/v1.1/chat"  # v1.5环境的地址
# Spark_url = "ws://spark-api.xf-yun.com/v2.1/chat"  # v2.0环境的地址

app = Flask(__name__)
CORS(app, origins="http://localhost:*", supports_credentials=True)
app.config["MONGO_URI"] = "mongodb://localhost:27017/test_app"
SECRET_KEY = "your_secret_key_here"

mongo = PyMongo(app)
UPLOAD_FOLDER = 'uploads'  # 设置上传文件夹

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

text = []
fans_score = 1
todo_score = 5
post_score = 2
if not os.path.exists('portrait'):
    os.makedirs('portrait')

text = []


def getText(role, content):
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = content
    text.append(jsoncon)
    return text


def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length


def checklen(text):
    while (getlength(text) > 8000):
        del text[0]
    return text


@app.route('/Spark', methods=['POST'])
def Spark():
    text.clear
    data = request.get_json()
    Input = data.get('question')
    question = checklen(getText("user", Input))
    SparkApi.answer = ""
    SparkApi.main(appid, api_key, api_secret, Spark_url, domain, question)
    getText("assistant", SparkApi.answer)
    return jsonify({'answer': SparkApi.answer})


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


@app.route('/video/<filename>', methods=['GET'])
def video(filename):
    return send_from_directory('./video', filename)


@app.route('/img/<filename>', methods=['GET'])
def img_person(filename):
    return send_from_directory('./portrait', filename)


@app.route('/portrait', methods=['GET'])
def image():
    token = request.headers.get('Authorization').split("Bearer ")[1]
    data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user_id = data["user_id"]
    print(user_id)
    users = mongo.db.users
    quire = {'user_id': user_id}
    user = users.find_one(quire)

    return jsonify(user['image'])


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
    url = 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'
    new_users = {"account": account, 'password': password, 'user_id': user_id, 'image': url}
    user.insert_one(new_users)
    return jsonify(user_id)


@app.route('/ballstage', methods=['GET'])
def ball_stage():
    try:
        token = request.headers.get('Authorization').split('Bearer ')[1]
        data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = data['user_id']
        print(user_id)
        user = mongo.db.users
        post = mongo.db.post
        todo = mongo.db.todo
        score = mongo.db.score
        sco = score.find_one({'user_id': user_id})
        fans_n = user.find_one({'user_id': user_id})['fans']
        post_n = post.count_documents({'user_id': user_id})
        todo_n = todo.find({'user_id': user_id})
        score1 = fans_n * fans_score
        score2 = post_n * post_score
        score3 = 0
        for t_n in todo_n:
            score3 += t_n['progress']
        print(score1, score2, score3)
        if not sco:
            score.insert_one({'user_id': user_id, 'fans_score': score1, 'post_score': score2,
                              'todo_score': score3, 'total': score1 + score2 + score3})
        else:
            update_date = {
                '$set': {
                    'fans_score': score1,
                    'post_score': score2,
                    'todo_score': score3,
                    'total': score1 + score2 + score3
                }
            }
            score.update_one({'user_id': user_id}, update_date)
        total = score1 + score2 + score3
        return jsonify(total/10000+1)
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired, please login again.'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/dailytodo', methods=['GET'])
def every_todo():
    try:
        token = request.headers.get('Authorization').split("Bearer ")[1]
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = data["user_id"]
        todos = mongo.db.todo
        today = datetime.datetime.now()
        results = todos.find(
            {'user_id': user_id, 'year': today.year, 'month': today.month, 'day': {'$lte': today.day}}).sort('day', -1)
        work = []
        if results:
            for result in results:
                t = result['tasks']
                time1 = 0
                time2 = 0
                already_do = 0
                for m in t:
                    time = int(m[3]) * 60 + int(m[4]) - int(m[1]) * 60 + int(m[2])
                    time2 += time
                    if m[6]:
                        time1 += time
                        already_do += 1
                result['plan_time'] = float(Decimal(time2 / 60).quantize(Decimal('0.00')))
                result['true_time'] = float(Decimal(time1 / 60).quantize(Decimal('0.00')))
                result['true_do'] = already_do
                # update_date = {
                #     '$set': {
                #         'progress': already_do/len(t)
                #     }
                # }
                # todos.update_one({'_id':result['_id']}, update_date)
                del result['_id']
                del result['user_id']
                del result['year']
                print(result)
                work.append(result)
            # print(work)
            return jsonify(work)
        else:
            return jsonify(work)
        return jsonify('success')
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired, please login again.'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/home/process', methods=['GET'])
def process():
    a = [random.random() for _ in range(6)]
    for i in range(24):
        a.append(-1)
    return jsonify(a)


@app.route('/home/todo', methods=['GET'])
def todo():
    try:
        token = request.headers.get('Authorization').split("Bearer ")[1]
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = data["user_id"]
        today = datetime.datetime.now()
        if user_id:
            users = mongo.db.todo
            quire = {'user_id': user_id, 'year': today.year, 'month': today.month, 'day': today.day}
            user = users.find_one(quire)
            if user:
                return jsonify({'tasks': user['tasks']})
            return jsonify({'tasks': []})
        return jsonify({'message': 'User not found'})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired, please login again.'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/home/todo/add', methods=['POST'])
def add():
    try:
        token = request.headers.get('Authorization').split("Bearer ")[1]
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = data["user_id"]
        todo = mongo.db.todo
        data1 = request.get_json()
        today = datetime.datetime.now()
        if user_id:
            users = mongo.db.todo
            quire = {'user_id': user_id, 'year': today.year, 'month': today.month, 'day': today.day}
            user = users.find_one(quire)
            if user:
                t = data1['tasks']
                already_do = 0
                for m in t:
                    already_do += m[6]
                update_date = {
                    '$set': {
                        'tasks': data1['tasks'],
                        'progress': already_do / len(data1['tasks']) * todo_score
                    }
                }
                users.update_one({'user_id': user_id, 'year': today.year, 'month': today.month, 'day': today.day},
                                 update_date)
            else:
                document = {'user_id': user_id, 'tasks': data1['tasks'], 'year': today.year, 'month': today.month,
                            'day': today.day, 'progress': 0}
                todo.insert_one(document)
        return jsonify('success')
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired, please login again.'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/home/todo/df', methods=['POST'])
def delete():
    try:
        token = request.headers.get('Authorization').split("Bearer ")[1]
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = data["user_id"]
        todo = mongo.db.todo
        data1 = request.get_json()
        today = datetime.datetime.now()
        if user_id:
            users = mongo.db.todo
            quire = {'user_id': user_id, 'year': today.year, 'month': today.month, 'day': today.day}
            user = users.find_one(quire)
            if user:
                t = data1['tasks']
                already_do = 0
                for m in t:
                    already_do += m[6]
                update_date = {
                    '$set': {
                        'tasks': data1['tasks'],
                        'progress': already_do / len(data1['tasks']) * todo_score
                    }
                }
                users.update_one({'user_id': user_id, 'year': today.year, 'month': today.month, 'day': today.day},
                                 update_date)
        return jsonify('success')
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired, please login again.'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500


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


@app.route('/changeimg', methods=['POST'])
def changeimg():
    token = request.headers.get('Authorization').split("Bearer ")[1]
    data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user_id = data["user_id"]
    if 'image' not in request.files:
        return jsonify({'err': '请上传图片'})
    file = request.files['image']
    if file == '':
        return jsonify({'err': '请选择图片'})
    path = './portrait/' + user_id
    if file:
        if os.path.exists(path):
            os.remove('./portrait/' + user_id)
        filepath = os.path.join('portrait', user_id)
        file.save(filepath)
        img_file = 'http://127.0.0.1:5000/img/' + user_id
        user = mongo.db.users
        update_date = {
            '$set': {
                'image': img_file
            }
        }
        user.update_one({'user_id': user_id},
                        update_date)
        print(img_file)
        return jsonify(img_file)


@app.route('/question', methods=['POST'])
def question():
    data = request.get_json()
    question = data.get('qa')
    userId = data.get('userId')
    learn = [question['0'], question['1'], question['2'], question['3'], question['4']]
    user = mongo.db.users
    update_date = {
        '$set': {
            'question': learn
        }
    }
    user.update_one({'userId': userId}, update_date)
    return jsonify('login success')


@app.route('/ocr', methods=['POST'])
def ocr():
    if 'image' not in request.files:
        return jsonify({'err': '请上传图片'})
    file = request.files['image']
    if file == '':
        return jsonify({'err': '请选择图片'})
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        appcode = "ff523a98c0cc486d9d128271b34b35a9"
        img_file = './uploads/' + file.filename
        params = {
            "configure": {
                "min_size": 16,  # 图片中文字的最小高度，单位像素（此参数目前已经废弃）
                "output_prob": True,  # 是否输出文字框的概率
                "output_keypoints": False,  # 是否输出文字框角点
                "skip_detection": False,  # 是否跳过文字检测步骤直接进行文字识别
                "without_predicting_direction": False,  # 是否关闭文字行方向预测
            }
        }
        result = OCR.reqs(appcode, img_file, params)
        return jsonify(result)


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
        today = datetime.datetime.now()
        time = str(today.year) + '-' + str(today.month) + '-' + str(today.day)
        image_data = None
        if img is not None:
            image_data = base64.b64decode(img)
        document = {'user_id': user_id, 'title': title, 'tag': tag, 'passage': passage, 'through': 0,
                    'like': 0, 'comment': 0, 'star': 0, 'time': time}
        if image_data:
            document['img'] = image_data
        post.insert_one(document)
        print(tag)
        return jsonify('success')
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired, please login again.'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/forum_heat', methods=['GET'])
def heat():
    post = mongo.db.post
    user = mongo.db.users
    results = list(post.find().sort('through', -1).limit(10))
    for result in results:
        result['_id'] = str(result['_id'])
        user_id = result['user_id']
        name = user.find_one({'user_id': user_id})['name']
        result['name'] = name
    # print(results)
    return jsonify(results)


@app.route('/postcontent', methods=['POST'])
def post_content():
    data = request.get_json()
    pg = data.get('pgId')
    post = mongo.db.post
    result = post.find_one({'_id': ObjectId(pg)})
    user = mongo.db.users
    user_id = result['user_id']
    us = user.find_one({'user_id': user_id})
    name = us['name']
    img = us['image']
    print(result)
    return jsonify({'title': result['title'], 'tag': result['tag'], 'description': result['passage'],
                    'pageView': result['through'], 'like': result['like'], 'follow': result['comment'],
                    'subscribe': result['star'], 'image': None, 'name': name, 'img': img, 'time': result['time']})


@app.route('/Person', methods=['GET'])
def person():
    try:
        token = request.headers.get('Authorization').split("Bearer ")[1]
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = data["user_id"]
        if user_id:
            users = mongo.db.users
            quire = {'user_id': user_id}
            user = users.find_one(quire)
            if user:
                return jsonify(
                    {'name': user['name'], 'account': user['account'], 'fans': user['fans'], 'post': user['posts'],
                     'follows': user['follows'], 'image': user['image'], 'userId': user['user_id'], 'sex': user['sex'],
                     'birth': user['birth'], 'degree': user['degree']})
        return jsonify({'message': 'User not found'})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired, please login again.'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
