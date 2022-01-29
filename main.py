import os
import struct
from json import dump, load
import argparse
import socket
from time import sleep
from peer_activity import *

global address
parser = argparse.ArgumentParser()
parser.add_argument("--ip", type=str, default="0")
args = parser.parse_args()
ip = args.ip
file_port = 29961

stateflag = -1
# -1 default, 0 second peer, 1 first



def discard_temps():
    list = traverse('./share')
    for file in list:
        if file.endswith('.temp'):
            os.remove(file)


def traverse(dir_path):
    listf = []
    folder_list = os.listdir(dir_path)
    for folder in folder_list:
        if os.path.isfile(os.path.join(dir_path, folder)):
            if folder[0] != '.':
                listf.append(os.path.join(dir_path, folder))
        else:
            listf.extend(traverse(os.path.join(dir_path, folder)))
    return listf

def firstpeer(initsocket, first_online):

    global stateflag
    global file_port
    global ip

    if first_online:
        #连接为空，开始创建套接字，绑定端口
        stateflag = 1
        try:
            initsocket.bind(('', file_port))
            initsocket.listen(2)
        except:
            pass
    global address
    filesocket, address = initsocket.accept()
    return filesocket


def transmissionloop(synchronized_history):
    global stateflag
    global ip
    global file_port
    initsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    initsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 套接字设置为可复用
    second_online = (stateflag != -1)
    if second_online:
        filesocket = None
    else:
        try:
            stateflag = 0
            initsocket.connect((ip, file_port))
            filesocket = initsocket
        except:
            filesocket = None
    if filesocket == None:
        first_online = (stateflag == -1 or stateflag == 0)
        filesocket = firstpeer(initsocket, first_online)
        print('no connection, waiting for another peer online...')
    else:
        print('connection established!!!')

    while True:
        try:
            # 连接建立后，循环收发
            send_and_receive(filesocket, synchronized_history)
            sleep(0.1)
            # 每0.1s进行一次扫描节约资源
        except:
            print('connection detached, need to restore...')
            break


def main():
    discard_temps()
    history = History()
    while True:
        transmissionloop(history)


if __name__ == '__main__':
    main()



