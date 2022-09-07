from time import sleep
import websockets as ws
from loguru import logger
from websockets import ConnectionClosed
import json
import httpx
import uuid
import asyncio

version = "v0.0.5"

whitelist = []
playerdata = {}
data = {}

try:
    logger.info("正在检测是否有新版本，请稍后")
    latest = json.loads(
        httpx.get("https://api.github.com/repos/zhishixiang/AutoWhitelist-Client/releases/latest").read())
    latest_version = latest["tag_name"]
    latest_description = latest["body"]
    if latest_version == version:
        logger.info("当前已为最新版本")
    else:
        logger.info("有新版本可下载，请前往GitHub下载")
        logger.info("更新内容摘要:" + latest_description)
except:
    logger.error("无法访问GitHub，请检查网络")

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


async def start():
    while True:
        uri = "wss://api.awl.bnnet.com.cn"
        try:
            async with ws.connect(uri) as websocket:
                logger.info("正在尝试注册，请稍后...")
                await websocket.send(str({"event": "register", "secret": secret}))
                not_registed = True
                while not_registed:
                    try:
                        response_str = await websocket.recv()
                        json_data = eval(response_str)
                        if json_data["event"] == "register" and json_data["status"] == "success":
                            logger.info("注册成功，开始接收请求")
                            not_registed = False
                            while True:
                                recv = await websocket.recv()
                                if recv == 1000:
                                    pass
                                else:
                                    json_data = eval(recv)
                                    if json_data["event"] == "newMission":
                                        await newMission(json_data, websocket)
                        elif json_data["event"] == "register" and json_data["status"] == "failed" and json_data["reason"] == "not registered":
                            logger.error("注册失败：该secret未注册")
                            assert()
                        else:
                            logger.error("注册失败：未知错误")
                            assert()
                    except ConnectionClosed as e:
                        print(e.code)
                        if e.code == 1006:
                            logger.error("断开连接，正在尝试重连...")
                            await asyncio.sleep(2)
                            break
        except ConnectionRefusedError as e:
            print(e)
            global count
            if count == 10:
                return
            count += 1
            await asyncio.sleep(2)


async def newMission(data, websocket):
    ID = data["ID"]
    print(data)
    event_id = data["eventID"]
    logger.info("新玩家%s已通过入服考试，即将添加白名单，事件ID:%s" % (ID, event_id))
    player_not_exist = True
    for i in whitelist:
        if i["name"] == ID:
            logger.error("白名单添加失败：该玩家已被添加")
            await websocket.send(
                str({"event": "callback", "status": "failed", "reason": "player already added", "secret": secret, "eventID": event_id}))
            logger.info("已发送回调，正在等待服务器确认收到")
            player_not_exist = False
            break
    if isOnline == "True":
        respond = httpx.get("https://api.mojang.com/users/profiles/minecraft/" + ID)
        if player_not_exist:
            if respond.status_code == 204:
                logger.error("白名单添加失败：该玩家不存在")
                await websocket.send(
                    str({"event": "callback", "status": "failed", "reason": "player not found", "secret": secret, "eventID": event_id}))
                logger.info("已发送回调，正在等待服务器确认收到")
            elif respond.status_code == 200:
                mojangData = json.loads(respond.read())
                playerdata['uuid'] = mojangData['id']
                playerdata['name'] = mojangData['name']
                for i in whitelist:
                    if i["uuid"] == playerdata['uuid']:
                        logger.error("白名单添加失败：该玩家已被添加")
                        await websocket.send(
                            str({"event": "callback", "status": "failed", "reason": "player already added", "secret": secret, "eventID": event_id}))
                        logger.info("已发送回调，正在等待服务器确认收到")
                        player_not_exist = False
                        break
                whitelist.append(playerdata)
    elif isOnline == "False":
        if player_not_exist:
            playerdata['uuid'] = str(uuid.uuid4())
            playerdata['name'] = ID
            whitelist.append(playerdata)

    else:
        logger.error("白名单添加失败：无法查询玩家信息，请确保网络畅通")
        await websocket.send(
            str({"event": "callback", "status": "failed", "reason": "network error", "secret": secret,
                 "eventID": event_id}))
    if player_not_exist:
        with open("whitelist.json", "w", encoding='UTF-8') as f:
            strwhitelist = str(whitelist).replace("'", "\"").replace(r"\n", "")
            f.write(strwhitelist)
            f.close()
        logger.info("白名单添加成功")
        await websocket.send(str({"event": "callback", "status": "success", "secret": secret, "eventID": event_id}))
        logger.info("已发送回调，正在等待服务器确认收到")
    resp = await websocket.recv()
    json_resp = eval(resp)
    for i in range(5):
        if json_resp["event"] == "callback" and json_resp["status"] == "received":
            logger.info("已确认服务器已收到回调")
            break
        elif i == 4:
            logger.error("服务器未收到回调，请检查服务器是否正常运行")
            break
        else:
            logger.info("未能确认服务器已收到回调，正在重试")
            sleep(3)



asyncio.get_event_loop().run_until_complete(start())
asyncio.get_event_loop().run_forever()
