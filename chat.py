# -*- coding: utf8 -*-
import json
import time
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

from pydub import AudioSegment
def fileTrans(akId, akSecret, appKey, fileLink) :
    # 地域ID，固定值。
    REGION_ID = "cn-shanghai"
    PRODUCT = "nls-filetrans"
    DOMAIN = "filetrans.cn-shanghai.aliyuncs.com"
    API_VERSION = "2018-08-17"
    POST_REQUEST_ACTION = "SubmitTask"
    GET_REQUEST_ACTION = "GetTaskResult"
    # 请求参数
    KEY_APP_KEY = "appkey"
    KEY_FILE_LINK = "file_link"
    KEY_VERSION = "version"
    KEY_ENABLE_WORDS = "enable_words"
    # 是否开启智能分轨
    KEY_AUTO_SPLIT = "auto_split"
    # 响应参数
    KEY_TASK = "Task"
    KEY_TASK_ID = "TaskId"
    KEY_STATUS_TEXT = "StatusText"
    KEY_RESULT = "Result"
    # 状态值
    STATUS_SUCCESS = "SUCCESS"
    STATUS_RUNNING = "RUNNING"
    STATUS_QUEUEING = "QUEUEING"
    # 创建AcsClient实例
    client = AcsClient(akId, akSecret, REGION_ID)
    # 提交录音文件识别请求
    postRequest = CommonRequest()
    postRequest.set_domain(DOMAIN)
    postRequest.set_version(API_VERSION)
    postRequest.set_product(PRODUCT)
    postRequest.set_action_name(POST_REQUEST_ACTION)
    postRequest.set_method('POST')
    # 新接入请使用4.0版本，已接入（默认2.0）如需维持现状，请注释掉该参数设置。
    # 设置是否输出词信息，默认为false，开启时需要设置version为4.0。
    task = {KEY_APP_KEY : appKey, KEY_FILE_LINK : fileLink, KEY_VERSION : "4.0", KEY_ENABLE_WORDS : False}
    # 开启智能分轨，如果开启智能分轨，task中设置KEY_AUTO_SPLIT为True。
    # task = {KEY_APP_KEY : appKey, KEY_FILE_LINK : fileLink, KEY_VERSION : "4.0", KEY_ENABLE_WORDS : False, KEY_AUTO_SPLIT : True}
    task = json.dumps(task)
    # print(task)
    postRequest.add_body_params(KEY_TASK, task)
    taskId = ""
    try :
        postResponse = client.do_action_with_exception(postRequest)
        postResponse = json.loads(postResponse)
        print (postResponse)
        statusText = postResponse[KEY_STATUS_TEXT]
        if statusText == STATUS_SUCCESS :
            print ("录音文件识别请求成功响应！")
            taskId = postResponse[KEY_TASK_ID]
        else :
            print ("录音文件识别请求失败！")
            return
    except ServerException as e:
        print (e)
    except ClientException as e:
        print (e)
    # 创建CommonRequest，设置任务ID。
    getRequest = CommonRequest()
    getRequest.set_domain(DOMAIN)
    getRequest.set_version(API_VERSION)
    getRequest.set_product(PRODUCT)
    getRequest.set_action_name(GET_REQUEST_ACTION)
    getRequest.set_method('GET')
    getRequest.add_query_param(KEY_TASK_ID, taskId)
    # 提交录音文件识别结果查询请求
    # 以轮询的方式进行识别结果的查询，直到服务端返回的状态描述符为"SUCCESS"、"SUCCESS_WITH_NO_VALID_FRAGMENT"，
    # 或者为错误描述，则结束轮询。
    statusText = ""
    while True :
        try :
            getResponse = client.do_action_with_exception(getRequest)
            getResponse = json.loads(getResponse)
            print (getResponse)
            statusText = getResponse[KEY_STATUS_TEXT]
            if statusText == STATUS_RUNNING or statusText == STATUS_QUEUEING :
                # 继续轮询
                time.sleep(10)
            else :
                # 退出轮询
                break
        except ServerException as e:
            print (e)
        except ClientException as e:
            print (e)
    if statusText == STATUS_SUCCESS :
        texts=""
        result = getResponse["Result"]
        sentences = result["Sentences"]
        maxlength = 5 #按长度分段
        for i,sentence in enumerate(sentences):
            index = i % (maxlength + 1)
            if index == maxlength:
                with open("recognition.txt","a+") as f:
                    f.write(texts+"\r\n\r\n")
                    print(texts)
                texts = ""
            text = sentence["Text"]
            texts +=text
            print(texts)
        print ("录音文件识别成功！")
    else :
        print ("录音文件识别失败！")
    return
def main():
    accessKeyId = "LTAI5tP5qXtKJcXkaq8keC1F"
    accessKeySecret = "BGGeJGUjIkQnpgKMhPAuxQpoAsPpQp"
    appKey = "gPrCs4ZhXrWYntPW"
    # fileLink = "https://gw.alipayobjects.com/os/bmw-prod/0574ee2e-f494-45a5-820f-63aee583045a.wav"
    # fileLink = "C:\\Users\\lenovo\\Desktop\\123.wav"
    fileLink = "https://12345zz.oss-cn-beijing.aliyuncs.com/123.wav?Expires=1693561331&OSSAccessKeyId=TMP.3KjYZjCtXLZSCoXV5G1FAJbaXvtixRhjTA5icw9YQGt46UGgacVUSN2pKGhn2U8pxUZJnEVBofqEhcCkByXMibmFZ4xbXU&Signature=vBuYNVPfV2UGjMr88XHB18PbXqE%3D"
    # 执行录音文件识别
    # wavSample(fileLink,fileLinks)
    fileTrans(accessKeyId, accessKeySecret, appKey, fileLink)

# def wavSample(from_path, to_path, frame_rate=16000, channels=1, startMin=0, endMin=None):
# 	# 根据文件的类型选择导入方法
#     audio = AudioSegment.from_wav(from_path)
#     # mp3_version = AudioSegment.from_mp3("never_gonna_give_you_up.mp3")
#     # ogg_version = AudioSegment.from_ogg("never_gonna_give_you_up.ogg")
#     # flv_version = AudioSegment.from_flv("never_gonna_give_you_up.flv")
#     startTime = startMin * 60 * 1000  # 单位ms
#     endTime = endMin * 60 * 1000 + 1 if endMin else None  # 单位ms
#     audio = audio[startTime:endTime]
#     mono = audio.set_frame_rate(frame_rate).set_channels(channels)  # 设置声道和采样率
#     mono.export(to_path, format='wav', codec='pcm_s16le')  # codec此参数本意是设定16bits pcm编码器

if __name__ == '__main__':
    # wavSample("C:\\Users\\lenovo\\Desktop\\录音.aac", "sample_new.WAV")
    main()
