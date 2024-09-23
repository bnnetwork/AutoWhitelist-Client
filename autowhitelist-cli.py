import os
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
"""
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
    key = config['key']
    isOnline = config['isOnline']
except:
    logger.error("读取配置文件失败，请检查配置文件是否存在且格式是否正确!")
    sys.exit(1)
try:
    with open("whitelist.json", "r", encoding='UTF-8') as f:
        whitelist = json.load(f)
    logger.info("读取白名单列表中")
    if not os.access("whitelist.json", os.W_OK):
        logger.error("没有whitelist.json的读写权限!")
        sys.exit(1)
    for i in whitelist:
        logger.info("uuid:" + i['uuid'])
        logger.info("name:" + i['name'])
    logger.info("读取完毕，请确认是否能正确读取")
except:
    logger.error("读取whitelist.json失败:文件为空，跳过读取步骤")


async def start(url):
    while True:
        try:
            async with websockets.connect(url) as websocket:
                await websocket.send(json.dumps({"code":0,"key":key}))
                recv_text = await websocket.recv()
                data = eval(recv_text)
                if(data["code"] == -1):
                    logger.critical("密钥不存在，请再次检查")
                    sys.exit(1)
                elif(data["code"] == -2):
                    logger.critical("客户端重复连接，请勿同时运行两个客户端")
                    sys.exit(1)
                elif data["code"] == 1:
                    server_name = data["server_name"]
                    logger.success("连接成功，服务器%s已上线"%server_name)
                else:
                    logger.error("未知的响应："+recv_text)
                    sys.exit(1)
                while True:
                    recv_text = await websocket.recv()
                    data = eval(recv_text)
                    try:
                        if data["code"] == 2:
                            player_name = data["msg"]
                            logger.info("新玩家%s已通过答题，正在添加白名单"%player_name)
                            for i in whitelist:
                                if i["name"] == player_name:
                                    logger.error("白名单添加失败：该玩家已被添加")
                                    break
                            if isOnline == "True":
                                # 如果是正版服则从mojang官网获取正版uuid
                                respond = httpx.get("https://api.mojang.com/users/profiles/minecraft/" + player_name)
                                if respond.status_code == 204:
                                    logger.error("白名单添加失败：该玩家不存在")
                                    continue
                                elif respond.status_code == 200:
                                    mojangData = json.loads(respond.read())
                                    playerdata['uuid'] = mojangData['id']
                                    playerdata['name'] = mojangData['name']
                                    for i in whitelist:
                                        if i["uuid"] == playerdata['uuid']:
                                            logger.error("白名单添加失败：该玩家已被添加")
                                            continue
                                        whitelist.append(playerdata)
                            elif isOnline == "False":
                                playerdata['uuid'] = str(uuid.uuid4())
                                playerdata['name'] = player_name
                                whitelist.append(playerdata)
                                with open("whitelist.json", "w", encoding='UTF-8') as f:
                                    strwhitelist = str(whitelist).replace("'", "\"").replace(r"\n", "")
                                    f.write(strwhitelist)
                                    f.close()
                                logger.info("白名单添加成功")
                            logger.success("新玩家%s添加成功"%player_name)
                            await websocket.send(json.dumps({"code":2,"message":"success"}))
                    except:
                        await websocket.send(json.dumps({"code":-2,"message":"failed"}))
                        logger.error("玩家%s添加失败，请复制以下信息联系开发者处理"%player_name)
                        traceback.print_exc()
        except websockets.exceptions.ConnectionClosedError:
            logger.error("WebSocket连接已关闭，正在尝试重新连接...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"发生错误：{e}，正在尝试重新连接...")
            await asyncio.sleep(5)


asyncio.get_event_loop().run_until_complete(start("wss://awl.toho.red/ws"))
