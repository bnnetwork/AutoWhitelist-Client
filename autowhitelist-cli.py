from time import sleep
import websockets
from loguru import logger
import json
import httpx
import uuid
import asyncio
import sys

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
        await websocket.send("123456")
        try:
            recv_text = await websocket.recv()
        except websockets.exceptions.ConnectionClosedError as e:
            if(eval(e.reason)["code"] == -1):
                logger.error("密钥错误，请再次检查")
            sys.exit(1)

        if recv_text == "ok":
            print(recv_text)
        for i in range(0,5):
            await websocket.send("hello")
        await websocket.close()



asyncio.get_event_loop().run_until_complete(start("ws://127.0.0.1:8765"))
