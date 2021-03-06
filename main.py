
import time
import json
import os

from paho.mqtt import client as mqtt_client

import serial

from dotenv import load_dotenv
load_dotenv()

import webbrowser


broker = os.environ['broker']
port = int(os.environ['port'])
username = os.environ['username']
password = os.environ['password']

player_name=""
before_match=True
go_on_match=True

class Sensor:
    def __init__(self):
        self.serial = serial.Serial('/dev/ttyUSB0', 115200)

    def read(self):
        data_str = self.serial.readline().decode()
        return int(data_str.split("\r")[0])   
 
def publish(client,topic,message):
    client.publish(topic,json.dumps(message))
    print(json.dumps(message))

# メッセージが届いたときの処理

def on_message(client, user_data, msg):
    global player_name
    global before_match 
    global go_on_match

    user_data_currently_connected=json.loads(msg.payload)
    if player_name!=user_data_currently_connected["name"]:
        before_match=False
    print(int(user_data_currently_connected["value"]))
    if int(user_data_currently_connected["value"])>=100:
        print("対戦終了　結果をブラウザで確認しよう!!")
        go_on_match=False
        client.loop_stop()
        
def on_connect(client, user_data, flags, rc):
    if rc == 0:
        print("サーバーに接続しました")
    else:
        print("Failed to connect, return code %d\n", rc)        



def connect_mqtt(client_user):
    client_id = 'device' + client_user
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port)
    return client


def get_standard_smell():
    print("基準値を取得しています")
    standard_value=0
    for i in range(10):
        standard_value+=int(Sensor().read())
    standard_value/=10
    return standard_value

def get_percent_smell(sum_smell):
    #kokoha ataiwokaenagarajikantyousei
    max_smell=10000.00
    
    rate_smell=int((sum_smell/max_smell)*100)
    return str(rate_smell)


def main():
    global before_match
    global go_on_match
    global player_name
    print("プレイヤー名を入力")
    player_name=input()

    print("合言葉を入力")
    topic=input()

    webbrowser.open("https://shugiou.vercel.app/")

    client = connect_mqtt(player_name)
    client.subscribe(topic)
    client.loop_start()

    #時間が10秒かかります
    standard_value=get_standard_smell()
    print("開始するには任意のキーを押してください")
    _ = input()
    sensor = Sensor()
    sum_smell=0.00
    while go_on_match:
        smell=sensor.read()
        #mainasuwohaijyo
        smell=float(smell-standard_value)+100
        rate_smell=get_percent_smell(sum_smell)
        #試合が始まっていないなら0を返す
        if before_match:
            rate_smell=str(0)
        else:
            sum_smell+=smell
        print(smell)
        message = {"name" :player_name,"value" : rate_smell}
        publish(client,topic,message)




if __name__ == '__main__':
    main()