from time import sleep
import websockets
from loguru import logger
import json
import httpx
import uuid
import asyncio
import sys
import traceback

version = "v0.0.5"

whitelist = []
playerdata = {}
data = {}
server_name = ""

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
"""
try:
    with open("awl.json", "r", encoding='UTF-8') as f:
        config = json.load(f)
    secret = config['secret']
    isOnline = config['isOnline']
except:
    logger.error("读取配置文件失败，请检查配置文件是否存在且格式是否正确")
    assert ()
"""
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


async def start(url):
     async with websockets.connect(url) as websocket:
        await websocket.send("1145141919810")
        try:
            recv_text = await websocket.recv()
        except websockets.exceptions.ConnectionClosedError as e:
            if(eval(e.reason)["code"] == -1):
                logger.critical("密钥错误，请再次检查")
                input("按Enter键退出")
            sys.exit(1)

        data = eval(recv_text)
        if data["code"] == 1:
            server_name = data["server_name"]
            logger.success("连接成功，服务器%s已上线"%server_name)
        while True:
            recv_text = await websocket.recv()
            data = eval(recv_text)
            try:
                if data["code"] == 2:
                    player_name = data["player_name"]
                    logger.info("新玩家%s已通过答题，正在添加白名单"%player_name)
                    logger.success("新玩家%s添加成功"%player_name)
                    await websocket.send(json.dumps({"code":2,"message":"success"}))
            except:
                await websocket.send(json.dumps({"code":-2,"message":"failed"}))
                logger.error("玩家%s添加失败，请复制以下信息联系开发者处理"%player_name)
                traceback.print_exc()


asyncio.get_event_loop().run_until_complete(start("ws://127.0.0.1:8765"))
