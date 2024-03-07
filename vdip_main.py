# ====================================================================================================
# Program :
# Developer : Straffic
# Date : 2024.01
# Description : vdip_main (vdu, ipu 통신 프로세스)
# ====================================================================================================

import os
import sys
import time
import select
import socket
import threading

from lib.lib_log import *
from lib.lib_cfg import *
from lib.lib_rabbitmq import *
from inc.val_def import *
from logic.vdip_recv import *
from logic.vdip_send import *
from lib.lib_taskman import *

# ----------------------------------------------------------------------------------------------------
# Function name : vdip_app_stop
# Function desc : 프로세스 종료 이벤트 수신
# ----------------------------------------------------------------------------------------------------
def vdip_app_stop(eid, data):
    global _exit_
    if eid == 1:  # 프로세스 종료
        print(data + ' ' + 'vdip_lnk process exit')
        log_info('vdip_lnk process exit')
        _exit_ = True
        sys.exit(1)
    else:
        print('vdip_lnk : received unknown event')
        print(eid)
        print(data)

def init_project() :
    app_name ='vdip_lnk'
    mcu_home = os.environ['MCU_HOME']
    log_home = os.environ['LOG_HOME']
    log_name = log_home + app_name + '.log'
    log_setting = mcu_home + 'config/logging.json'

    event_fun = vdip_app_stop
    AppHealthChecker(app_name, event_fun).start()

    if log_init(app_name, log_setting, log_name) == False:
        log_error("[MCU <-> VDU, IPU] Process Error - Check config file and log path")
        log_error('Config file Path = ' + log_setting)
        log_error('Logfile Path = ' + log_home)
        sys.exit(-1)

    if not cfg_init():
        log_error('[MCU <-> VDU, IPU] Process Error - Check cfg_init()')
        sys.exit(-1)
    main()

def insert_cmd_q():
    queue_msg = '36010000000000000000'
    rmq_publish_cmd(queue_msg)
    threading.Timer(0.5, insert_cmd_q).start()


def main():
    # RqbbitMq 연결
    mq_init()

    # MCU ip, port설정 MCU <-> VDU, IPU port : 20355
    mcu_ip = cfg_get_equipment_ip()
    vdip_port = int(20333)

    # 소켓 설정
    lsn_mcu = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsn_mcu.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lsn_mcu.bind((mcu_ip, vdip_port))
    lsn_mcu.listen()
    socket_list = [lsn_mcu, ]

    threading.Thread(target=insert_cmd_q).start()

    while True :
        try :
            read_sock, _, _ = select.select(socket_list, [], [], 1)
            for sock in read_sock:
                if sock in socket_list:
                    client_socket, addr = sock.accept()
                    log_info("connect = " + str(addr))
                    if sock == lsn_mcu:
                        send_thread = threading.Thread(target=send_msg, args=(client_socket,))
                        recv_thread = threading.Thread(target=recv_msg, args=(client_socket,))

                        send_thread.daemon = True
                        recv_thread.daemon = True

                        send_thread.start()
                        recv_thread.start()
        except Exception as e:
            log_error("Check connection: " + str(e))

def send_msg(client_socket):


def recv_msg(client_socket) :
    

if __name__ == "__main__":
   init_project()



