import asyncio
import socket
import time

import websockets
import os
import ctypes
import threading
import subprocess

from queue import Queue
q = Queue()



def int_overflow(val):
    maxint = 2147483647
    if not -maxint-1 <= val <= maxint:
        val = (val + (maxint + 1)) % (2 * (maxint + 1)) - maxint -1
    return val


def unsigned_right_shitf(n, i):
    if n < 0:
        n = ctypes.c_uint32(n).value
    if i < 0:
        return -int_overflow(n << abs(i))
    return int_overflow(n >> i)


def start_server():
    while True:
        print("zuse")
        flag = q.get()
        print(flag)
        if flag:
            print("start")
            os.system("adb forward tcp:22222 tcp:6612")
            os.system("adb push ./server-debug.apk /data/local/tmp")
            os.system("adb shell CLASSPATH=/data/local/tmp/server-debug.apk app_process / com.genymobile.scrcpy.Server 1.24 log_level=info")



async def echo(websocket, path):
    client =socket.socket()
    revc_data = await websocket.recv()
    print(revc_data)

    q.put(True)
    print("start send jpeg")
    time.sleep(1)

    a = socket.socket()
    client.connect(("127.0.0.1", 22222))

    a.connect(("127.0.0.1", 22222))
    readBannerBytes = 0
    bannerLength = 2
    readFrameBytes = 0
    frameBodyLength = 0
    frameBody = bytes()
    banner = {
        "version": 0,
        "length": 0,
        "pid": 0,
        "realWidth": 0,
        "realHeight": 0,
        "virtualWidth": 0,
        "virtualHeight": 0,
        "orientation": 0,
        "quirks": 0
    }

    while True:
        chunk = client.recv(1024)
        cursor = 0
        while cursor < len(chunk):
            if readBannerBytes < bannerLength:
                if readBannerBytes == 0:
                    banner["version"] = chunk[cursor]
                elif readBannerBytes == 1:
                    banner["length"] = bannerLength = chunk[cursor]
                elif readBannerBytes == 5:
                    banner["pid"] += unsigned_right_shitf((chunk[cursor] << ((readBannerBytes - 2) * 8)), 0)
                elif readBannerBytes == 9:
                    banner["realWidth"] += unsigned_right_shitf((chunk[cursor] << ((readBannerBytes - 6) * 8)), 0)
                elif readBannerBytes == 13:
                    banner["realHeight"] += unsigned_right_shitf((chunk[cursor] << ((readBannerBytes - 10) * 8)), 0)
                elif readBannerBytes == 17:
                    banner["virtualWidth"] += unsigned_right_shitf((chunk[cursor] << ((readBannerBytes - 14) * 8)), 0)
                elif readBannerBytes == 21:
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
                print("frameBodyLength:", frameBodyLength)
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


t = threading.Thread(target=start_server, args=())
t.start()
start_server = websockets.serve(echo, "127.0.0.1", 9002)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
