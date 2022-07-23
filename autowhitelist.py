from time import sleep
import socketio
from loguru import logger

secret = "voIao2v4ywPZgosp"
sio = socketio.Client()


@sio.on('connect')
def on_connect():
    logger.info('正在注册，请稍后')
    sleep(2)
    sid = sio.get_sid(namespace='/mission')
    sio.emit('register', {'secret': secret, 'sid': sid})


@sio.on('register')
def isReg(data):
    if data['status'] == "success":
        logger.info("注册成功 ，当前 token 为" + data['token'])
        pass
    elif data['status'] == "failed":
        logger.error("注册失败：secret不存在")
        sleep(1)
        input("按enter键继续")
        assert()
    else:
        logger.error("注册失败：未知错误")
        sleep(1)
        input("按enter键继续")
        assert()


@sio.on("newMission", namespace='/mission')
def newMission(data):
    id = data["id"]
    logger.info("新玩家%s已通过入服考试，即将添加白名单" % id)
    return "success"


sio.connect('ws://127.0.0.1:8090/')
sio.wait()
