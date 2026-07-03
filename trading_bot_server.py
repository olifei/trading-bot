#!/usr/bin/env python3

import asyncio
import json
import os
import signal
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import logging
import firebase_admin
from pathlib import Path
from dotenv import load_dotenv

from trading_assistant.agent import root_agent
from trading_assistant.services.database.firestore_client import get_firestore_client

dotenv_path = Path.cwd() / 'trading_assistant' / '.env'
load_dotenv(dotenv_path=dotenv_path)
logger_dotenv = logging.getLogger("dotenv_loader")
if dotenv_path.exists():
    logger_dotenv.info(f"Successfully loaded .env file from {dotenv_path}")
else:
    logger_dotenv.warning(f".env file not found at {dotenv_path}. API keys might be missing.")


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("trading_bot_server")

sessions = {}

# Socket服务器设置
SERVER_ADDRESS = './trading_bot_socket'
MAX_BUFFER_SIZE = 65536

async def process_message(user_id, message):
    global sessions
    
    if user_id not in sessions:
        logger.info(f"为用户 {user_id} 创建新会话")
        session_service = InMemorySessionService()
        
        app_name = "trading_bot"
        runner = Runner(
            agent=root_agent,
            app_name=app_name,
            session_service=session_service
        )
        
        session_id = f"{user_id}_session"
        
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state={"user_id": user_id}
        )
        
        sessions[user_id] = (session_service, runner, session_id)
        logger.info(f"会话已创建，ID: {session_id}")
    else:
        logger.info(f"使用用户 {user_id} 的现有会话")
        session_service, runner, session_id = sessions[user_id]
    
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=message)]
    )
    
    responses = []
    
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message
        ):
            if hasattr(event, 'content') and event.content:
                parts = event.content.parts if hasattr(event.content, 'parts') else []
                if parts and hasattr(parts[0], 'text') and parts[0].text:
                    responses.append({
                        "author": event.author,
                        "text": parts[0].text
                    })
            elif hasattr(event, 'error_message') and event.error_message:
                responses.append({
                    "author": "error",
                    "text": event.error_message
                })
    except Exception as e:
        logger.error(f"处理消息时出错: {str(e)}")
        responses.append({
            "author": "error",
            "text": f"处理消息时出错: {str(e)}"
        })
    
    return responses

async def handle_client(reader, writer):
    try:
        data = await reader.read(MAX_BUFFER_SIZE)
        message = data.decode()
        
        try:
            request = json.loads(message)
            user_id = request.get('user_id')
            message_text = request.get('message')
            
            if not user_id or not message_text:
                response = {"error": "请求缺少user_id或message字段"}
                writer.write(json.dumps(response).encode())
                await writer.drain()
                return
            
            responses = await process_message(user_id, message_text)
            
            writer.write(json.dumps(responses).encode())
            await writer.drain()
            
        except json.JSONDecodeError:
            response = {"error": "无效的JSON请求"}
            writer.write(json.dumps(response).encode())
            await writer.drain()
    
    except Exception as e:
        logger.error(f"处理客户端请求时出错: {str(e)}")
        try:
            response = {"error": f"处理请求时出错: {str(e)}"}
            writer.write(json.dumps(response).encode())
            await writer.drain()
        except:
            pass
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    try:
        if os.path.exists(SERVER_ADDRESS):
            os.unlink(SERVER_ADDRESS)
    except OSError:
        pass
    
    server = await asyncio.start_unix_server(handle_client, SERVER_ADDRESS)
    os.chmod(SERVER_ADDRESS, 0o777)
    logger.info(f"服务器已启动于 {SERVER_ADDRESS}")
    
    loop = asyncio.get_running_loop()
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(
            getattr(signal, signame),
            lambda: asyncio.create_task(shutdown(loop, server))
        )
    
    try:
        try:
            firebase_admin.get_app()
            logger.info("Firebase Admin SDK已经初始化。")
        except ValueError:
            logger.info("正在初始化Firebase Admin SDK (默认配置)...")
            firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK初始化完成。")
        try:
            get_firestore_client() 
            logger.info("Firestore client is accessible.")
        except Exception as e_firestore:
            logger.error(f"首次访问Firestore客户端失败: {e_firestore}", exc_info=True)

        async with server:
            await server.serve_forever()
    except asyncio.CancelledError:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器主循环发生未捕获的异常: {e}", exc_info=True)


async def shutdown(loop, server):
    logger.info("关闭服务器...")
    server.close()
    await server.wait_closed()
    
    try:
        os.unlink(SERVER_ADDRESS)
    except OSError:
        pass
    
    loop.stop()

def run_server():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("收到中断信号，服务器已停止")

if __name__ == "__main__":
    run_server()
