import asyncio

import websockets
import os
import json
import ctypes


loop = asyncio.get_event_loop()

banner = {"version": 0, "length": 0, "pid": 0, "realWidth": 0, "realHeight": 0, "virtualWidth": 0,
          "virtualHeight": 0, "orientation": 0, "quirks": 0}


def int_overflow(val):
    maxint = 2147483647
    if not -maxint - 1 <= val <= maxint:
        val = (val + (maxint + 1)) % (2 * (maxint + 1)) - maxint - 1
    return val


def unsigned_right_shitf(n, i):
    if n < 0:
        n = ctypes.c_uint32(n).value
    if i < 0:
        return -int_overflow(n << abs(i))
    return int_overflow(n >> i)


async def start_server():
    os.popen("adb forward tcp:22222 tcp:6612")
    os.popen("adb push ./server-debug.apk /data/local/tmp")
    os.popen("adb shell CLASSPATH=/data/local/tmp/server-debug.apk app_process / "
             "com.genymobile.scrcpy.Server 1.24 log_level=info")


async def start_audio_server():
    os.popen("adb forward tcp:28200 localabstract:sndcpy")
    os.popen("adb shell am start com.rom1v.sndcpy/.MainActivity")


async def install_sndcpy_apk():
    os.popen("sndcpy.bat")


async def recv_data(websocket, writer):
    while True:
        msg = await websocket.recv()
        try:
            print(msg)
            json_msg = json.loads(msg)
            if json_msg["msg_inject_touch_position"]["width"] < json_msg["msg_inject_touch_position"]["height"]:
                pass
            width = banner['realWidth']
            height = banner['realHeight']
            if json_msg["msg_inject_touch_position"]["width"] > json_msg["msg_inject_touch_position"]["height"]:
                width = banner['realHeight']
                height = banner['realWidth']
            x = int((json_msg["msg_inject_touch_position"]["x"] / json_msg["msg_inject_touch_position"]["width"]) * width)
            y = int((json_msg["msg_inject_touch_position"]["y"] / json_msg["msg_inject_touch_position"]["height"]) * height)
            t = int.to_bytes(json_msg['msg_type'], length=1, byteorder='big') +\
                int.to_bytes(json_msg['msg_inject_touch_action'], length=1, byteorder='big') +\
                int.to_bytes(-1, length=8, byteorder='big', signed=True) +\
                int.to_bytes(x, length=4, byteorder='big') +\
                int.to_bytes(y, length=4, byteorder='big') +\
                int.to_bytes(width, length=2, byteorder='big') +\
                int.to_bytes(height, length=2, byteorder='big') + \
                int.to_bytes(65535, length=2, byteorder='big') +\
                int.to_bytes(1, length=4, byteorder='big')
            writer.write(t)
        except Exception as err:
            print('this is error')
            print(str(err))


async def send_data(websocket, reader):
    readBannerBytes = 0
    bannerLength = 2
    readFrameBytes = 0
    frameBodyLength = 0
    frameBody = bytes()

    while True:
        chunk = await reader.read(1024)
        cursor = 0
        while cursor < len(chunk):
            if readBannerBytes < bannerLength:
                if readBannerBytes == 0:
                    banner["version"] = chunk[cursor]
                elif readBannerBytes == 1:
                    banner["length"] = bannerLength = chunk[cursor]
                elif readBannerBytes in (2, 3, 4, 5):
                    banner["pid"] += unsigned_right_shitf((chunk[cursor] << ((readBannerBytes - 2) * 8)), 0)
                elif readBannerBytes in (6, 7, 8, 9):
                    banner["realWidth"] += unsigned_right_shitf((chunk[cursor] << ((readBannerBytes - 6) * 8)), 0)
                elif readBannerBytes in (10, 11, 12, 13):
                    banner["realHeight"] += unsigned_right_shitf((chunk[cursor] << ((readBannerBytes - 10) * 8)), 0)
                elif readBannerBytes in (14, 15, 16, 17):
                    banner["virtualWidth"] += unsigned_right_shitf((chunk[cursor] << ((readBannerBytes - 14) * 8)), 0)
                elif readBannerBytes in (18, 19, 20, 21):
                    banner["virtualHeight"] += unsigned_right_shitf((chunk[cursor] << ((readBannerBytes - 18) * 8)), 0)
                elif readBannerBytes == 22:
                    banner["orientation"] = chunk[cursor] * 90
                elif readBannerBytes == 23:
                    banner["quirks"] = chunk[cursor]
                cursor += 1
                readBannerBytes += 1

                if readBannerBytes == bannerLength:
                    print("banner:", banner)
            elif readFrameBytes < 4:
                frameBodyLength += unsigned_right_shitf((chunk[cursor] << (readFrameBytes * 8)), 0)
                cursor += 1
                readFrameBytes += 1
            else:
                if (len(chunk) - cursor >= frameBodyLength):
                    frameBody = frameBody + bytes(chunk[cursor: frameBodyLength])
                    if len(frameBody):
                        if frameBody[0] != 255 or frameBody[1] != 216:
                            print("Frame body does not start with JPG header", frameBody)
                        else:
                            await websocket.send(frameBody)
                    cursor += frameBodyLength
                    frameBodyLength = readFrameBytes = 0
                    frameBody = bytes()
                else:
                    frameBody = frameBody + bytes(chunk[cursor: len(chunk)])
                    frameBodyLength -= len(chunk) - cursor
                    readFrameBytes += len(chunk) - cursor
                    cursor = len(chunk)

async def send_audio_data(websocket, reader):
    print('start revc')
    while True:
        chunk = await reader.read(1440)
        # print(chunk)
        await websocket.send(chunk)


async def echo(websocket, path):
    print(path)
    if path == '/':
        pass
        t1 = asyncio.create_task(start_server())
        await asyncio.sleep(1)
        reader, writer = await asyncio.open_connection("127.0.0.1", 22222, loop=loop)
        control_reader, control_writer = await asyncio.open_connection("127.0.0.1", 22222, loop=loop)
        t2 = asyncio.create_task(send_data(websocket, reader))
        t3 = asyncio.create_task(recv_data(websocket, control_writer))
        await t1
        await t2
        await t3
    elif path == '/audio':
        t4 = asyncio.create_task(start_audio_server())
        await asyncio.sleep(1)
        audio_reader, audio_writer = await asyncio.open_connection("127.0.0.1", 28200, loop=loop)
        print(audio_reader)
        t5 = asyncio.create_task(send_audio_data(websocket, audio_reader))
        await t4
        await t5
    elif path == '/install':
        await asyncio.create_task(install_sndcpy_apk())


loop.run_until_complete(websockets.serve(echo, "127.0.0.1", 9002))
loop.run_forever()
