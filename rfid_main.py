import os
import sys
import time

from inc.val_def import *
from lib.lib_log import *
from lib.lib_cfg import *
from lib.lib_rabbitmq import *
from lib.lib_taskman import *

from logic.rfid_event import *
from logic.rfid_command import *


def rfid_app_stop(eid, data):
    global _exit_
    if eid == 1:  # 프로세스 종료
        print(data + ' ' + 'rfid_lnk process exit')
        log_info('rfid_lnk process exit')
        _exit_ = True
        sys.exit(1)
    else:
        print('rfid_lnk : received unknown event')
        print(eid)
        print(data)


if __name__ == "__main__" :
    app_name = 'rfid_lnk'
    mcu_home = os.environ['MCU_HOME']
    log_home = os.environ['LOG_HOME']
    log_name = log_home + app_name + '.log'
    log_setting = mcu_home + 'config/logging.json'

    if log_init(app_name, log_setting, log_name) == False:
        log_error("[MCU <-> RFID] Process Error - Check config file and log path")
        log_error('Config file Path = ' + log_setting)
        log_error('Logfile Path = ' + log_home)
        sys.exit(-1)

    if not cfg_init():
        log_error('[MCU <-> RFID] Process Error - Check cfg_init()')
        sys.exit(-1)

    rfid_ip = cfg_get_rfid_ip()
    event_port = int(cfg_get_event_port())
    command_port = int(cfg_get_command_port())

    # RMQ init
    mq_init()
    # Channel ID init
    Default_setting.channel_id = -999

    event_fun = rfid_app_stop
    AppHealthChecker(app_name, event_fun).start()

    # Event thread, Recv Channel if
    event_channel = Event_Thread(rfid_ip, event_port)
    event_channel.start()

    # 메인 스레드는 channel_id 를 수신할 때 까지 channel_id 체크
    while True:
        # 채널 id 가 -998 이면 이벤트 채널 연결을 실패한것이므로 시스템 종료
        if Default_setting.channel_id == -998:
            sys.exit(-1)
        # 채널 id 가 초기값(-999), 연결종료(-998) 가 아닌 정상 수신한것이라면 반복문 종료
        elif Default_setting.channel_id != -999:
            break

    # channel_id 가 수신되면 Command Thread 시작
    if Default_setting.channel_id != -999:
        command_channel = Command_Thread(rfid_ip, command_port)
        command_channel.start()

        # 커맨드 채널은 연결을 실패했을 경우 아래 로직에서 자동으로 종료됨.
        # 이벤트 채널, 커맨드 채널 정상 처리 후 1분후 부터 10초 간격으로 스레드 상태 체크
        try :
            time.sleep(60)
            while True:
                log_debug(f"[Check] Event thread = {event_channel.is_alive()} / Command thread = {command_channel.is_alive()}")
                if event_channel.is_alive() == False or command_channel.is_alive() == False:
                    log_debug("[Check] thread Error")
                    event_channel.stop()
                    command_channel.stop()
                    #event_channel.join()
                    #command_channel.join()
                    log_debug("[Check] Stop thread success.. exit system")
                    sys.exit(-1)
                time.sleep(60)
        except Exception as e:
            log_error("Thread check error " + str(e))

