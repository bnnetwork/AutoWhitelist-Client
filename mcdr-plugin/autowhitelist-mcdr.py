import websockets
import json
import asyncio
import traceback
from mcdreforged.api.all import *

PLUGIN_METADATA = {
    'id': 'autowhitelist',
    'version': '0.0.1',
    'name': 'autowhitelist',
    "description": "Automaticly add whitelist by tests",
    "author": "zsx",
}
key = "1"
url = "wss://awl.toho.red/ws"
server_thread = None

"""
try:
    server.logger.info("正在检测是否有新版本，请稍后")
    latest = json.loads(
        httpx.get("https://api.github.com/repos/zhishixiang/AutoWhitelist-Client/releases/latest").read())
    latest_version = latest["tag_name"]
    latest_description = latest["body"]
    if latest_version == version:
        server.logger.info("当前已为最新版本")
    else:
        server.logger.info("有新版本可下载，请前往GitHub下载")
        server.logger.info("更新内容摘要:" + latest_description)
except:
    server.logger.error("无法访问GitHub，请检查网络")
"""
def kill_server(server):
    server.logger.info("autowhitelist正在停止服务...")

async def start(server):
    while True:
        try:
            async with websockets.connect(url) as websocket:
                await websocket.send(json.dumps({"code":0,"key":key}))
                recv_text = await websocket.recv()
                data = eval(recv_text)
                if data["code"] == -1:
                    server.logger.critical("密钥不存在，请再次检查")
                    break
                elif data["code"] == -2:
                    server.logger.critical("客户端重复连接，请勿同时运行两个客户端")
                    break
                elif data["code"] == 1:
                    server_name = data["server_name"]
                    server.logger.info(f"连接成功，服务器{server_name}已上线")
                else:
                    server.logger.error(f"未知的响应：{recv_text}")
                    break

                while True:
                    recv_text = await websocket.recv()
                    data = eval(recv_text)
                    try:
                        if data["code"] == 2:
                            player_name = data["msg"]
                            server.logger.info(f"新玩家{player_name}已通过答题，正在添加白名单")
                            server.execute(f"whitelist add {player_name}")
                            server.logger.info(f"新玩家{player_name}添加成功")
                            await websocket.send(json.dumps({"code":2,"message":"success"}))
                    except:
                        await websocket.send(json.dumps({"code":-2,"message":"failed"}))
                        server.logger.error(f"玩家{player_name}添加失败，请复制以下信息联系开发者处理")
                        traceback.print_exc()
        except websockets.exceptions.ConnectionClosedError:
            server.logger.error("WebSocket连接已关闭，正在尝试重新连接...")
            await asyncio.sleep(5)
        except Exception as e:
            server.logger.error(f"发生错误：{e}，正在尝试重新连接...")
            await asyncio.sleep(5)

@new_thread('Autowhitelist Client Thread')
def start_thread(server):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start(server))
    finally:
        loop.close()

def on_load(server: ServerInterface, old):
    server.logger.info("autowhitelist已被加载，正在等待服务启动...")
    global server_thread
    server_thread = start_thread(server)

def on_server_stop(server: PluginServerInterface, server_return_code: int):
    kill_server(server)

def mcdr_stop(server:PluginServerInterface):
    kill_server(server)
