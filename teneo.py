import asyncio
import random
import ssl
import json
import time
import uuid
import os
from loguru import logger
import websockets
from fake_useragent import UserAgent
banner = """\033[36m
████████╗███████╗███╗   ██╗███████╗ ██████╗ 
╚══██╔══╝██╔════╝████╗  ██║██╔════╝██╔═══██╗
   ██║   █████╗  ██╔██╗ ██║█████╗  ██║   ██║
   ██║   ██╔══╝  ██║╚██╗██║██╔══╝  ██║   ██║
   ██║   ███████╗██║ ╚████║███████╗╚██████╔╝
   ╚═╝   ╚══════╝╚═╝  ╚═══╝╚══════╝ ╚═════╝ Node
------------------------------------------------
            Author : Sahal Pramudya
------------------------------------------------\n"""
# Get a random User-Agent for requests
useragent = UserAgent(os='windows', platforms='pc', browsers='chrome')
user_agent = useragent.random
print(banner)
user_id = input("Masukkan User ID : ")#'95f0d9f5-6515-484a-849d-19993b34ad87'
uri = 'wss://secure.ws.teneo.pro/websocket?userId={}&version=v0.2'.format(user_id)


async def send_ping(websocket):
    """Function to send PING messages at intervals."""
    while True:
        try:
            send_message = json.dumps({"type": "PING"})
            logger.debug(f"Sending PING: {send_message}")
            await websocket.send(send_message)
            await asyncio.sleep(5)  # Adjust this interval as needed
        except Exception as e:
            logger.error(f"Error in send_ping: {e}")
            break  # Exit if an error occurs

async def handle_messages(websocket, user_id, user_agent):
    """Function to handle incoming messages from the WebSocket."""
    while True:
        try:
            response = await websocket.recv()
            message = json.loads(response)
            logger.info(f"Received message: {message}")

            if message.get("message") == "Connected successfully":
                auth_response = {
                    "date":message['date'],
                    "pointsToday":message['pointsToday'],
                    "pointsTotal":message['pointsTotal'],
                    "message":message['message'],
                    "isNewUser":"false"
                }
                logger.debug(f"Sending AUTH response: {auth_response}")
                await websocket.send(json.dumps(auth_response))

            elif message.get("type") == "PING":
                pong_response = {"type":"PING"}
                logger.debug(f"Sending PING PONG response: {pong_response}")
                await websocket.send(json.dumps(pong_response))

        except websockets.ConnectionClosed:
            logger.warning("WebSocket connection closed. Attempting to reconnect...")
            break  # Break to reconnect
        except Exception as e:
            logger.error(f"Error while receiving message: {e}")
            break  # Break to reconnect

async def connect_to_wss(user_id):
    device_id = str(uuid.uuid4())
    logger.info(f"Connecting with Device ID: {device_id}")
    
    backoff_time = 1  # Initial backoff time in seconds
    uri_index = 0  # Start with the first URI

    while True:  # Main loop for connection attempts
        try:
            await asyncio.sleep(random.uniform(0.1, 1))  # Random delay before connecting
            custom_headers = {
                "User-Agent": user_agent,
                "Origin": "chrome-extension://emcclcoaglgcpoognfiggmhnhgabppkm"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            async with websockets.connect(uri, ssl=ssl_context, extra_headers=custom_headers) as websocket:
                logger.info(f"WebSocket connected to URI: {uri}")

                # Start sending PING messages
                asyncio.create_task(send_ping(websocket))
                
                # Handle incoming messages
                await handle_messages(websocket, user_id, custom_headers['User-Agent'])

        except Exception as e:
            logger.error(f"Connection error: {e} with URI: {uri}")
            logger.info(f"Retrying with a different URI in {backoff_time} seconds...")

            # Increment to switch to the next URI
            uri_index = (uri_index + 1) % len(ws_uris)  # Cycle through URIs
            
            await asyncio.sleep(backoff_time)
            backoff_time = min(backoff_time * 2, 30)  # Exponential backoff with a cap
async def main():
    await connect_to_wss(user_id)

if __name__ == '__main__':
    asyncio.run(main())
