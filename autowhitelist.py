from time import sleep
import socketio
from loguru import logger
import json
import httpx
import uuid
version = "v0.0.4"

sio = socketio.Client()
sio.eio.ping_interval = 30
sio.eio.ping_timeout = 30

whitelist = []
playerdata = {}

try:
    logger.info("正在检测是否有新版本，请稍后")
    latest = json.loads(httpx.get("https://api.github.com/repos/zhishixiang/AutoWhitelist-Client/releases/latest").read())
    latest_version = latest["tag_name"]
    if latest_version == version:
        logger.info("当前已为最新版本")
    else:
        logger.info("有新版本可下载，请前往GitHub下载")
except:
    logger.error("无法连接GitHub，请检查网络")

try:
    with open("awl.json", "r", encoding='UTF-8') as f:
        config = json.load(f)
    secret = config['secret']
    isOnline = config['isOnline']
except:
    logger.error("读取配置文件失败，请检查配置文件是否存在且格式是否正确")
    assert ()

try:
    with open("whitelist.json", "r", encoding='UTF-8') as f:
        whitelist = json.load(f)
    logger.info("读取白名单列表中")
    for i in whitelist:
        logger.info("uuid:" + i['uuid'])
        logger.info("name:" + i['name'])
    logger.info("读取完毕，请确认是否能正确读取")
except:
    logger.error("读取whitelist.json失败:文件为空，跳过读取步骤")


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
        assert ()
    else:
        logger.error("注册失败：未知错误")
        sleep(1)
        input("按enter键继续")
        assert ()


@sio.on("newMission", namespace='/mission')
def newMission(data):
    id = data["id"]
    logger.info("新玩家%s已通过入服考试，即将添加白名单" % id)
    if isOnline == "True":
        respond = httpx.get("https://api.mojang.com/users/profiles/minecraft/" + id)
        for i in whitelist:
            if i["name"] == id:
                return {"status": "failed", "reason": "player exist", "secret": secret}
        if respond.status_code == 204:
            logger.error("白名单添加失败：该玩家不存在")
            return {"status": "failed", "reason": "player not found", "secret": secret}
        elif respond.status_code == 200:
            mojangData = json.loads(respond.read())
            playerdata['uuid'] = mojangData['uuid']
            playerdata['name'] = mojangData['id']
            whitelist.append(playerdata)
    elif isOnline == "False":
        playerdata['uuid'] = str(uuid.uuid4())
        playerdata['name'] = id

    else:
        logger.error("白名单添加失败：无法查询玩家信息，请确保网络畅通")
        return {"status": "failed", "reason": "network error", "secret": secret}
    
    with open("whitelist.json", "w", encoding='UTF-8') as f:
        strwhitelist = str(whitelist).replace("'", "\"").replace(r"\n", "")
        print(strwhitelist)
        f.write(strwhitelist)
        f.close()
    logger.info("白名单添加成功")
    return {"status": "success", "secret": secret}


sio.connect('wss://api.awl.bnnet.com.cn/')
sio.wait()
