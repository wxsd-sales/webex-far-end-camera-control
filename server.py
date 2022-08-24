#!/usr/bin/env python
#from distutils import command
#from inspect import trace
import base64
import os
import json
#import pytz
#import re
import traceback

import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web

#from mongo_db_controller import UserDB
from settings import Settings
from spark import Spark
from handlers.base import BaseHandler
from handlers.oauth import WebexOAuthHandler

#from datetime import datetime, timedelta
#from dateutil import parser
#from pymongo import ASCENDING, DESCENDING
from tornado.options import define, options, parse_command_line
from tornado.httpclient import HTTPError
#from uuid import uuid4

define("debug", default=False, help="run in debug mode")

class DeviceBot(object):
    spark = Spark(Settings.bot_token)

class AuthFailedHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        try:
            print("AuthFailedHandler GET")
            self.render("authentication-failed.html")
        except Exception as e:
            traceback.print_exc()

class MainHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        try:
            print("MainHandler GET")
            self.load_page(state="?"+self.request.query)
        except Exception as e:
            traceback.print_exc()


class CommandHandler(BaseHandler):
    @tornado.gen.coroutine
    def post(self):
        print("CommandHandler request.body:{0}".format(self.request.body))
        jbody = json.loads(self.request.body)
        command = jbody.get('command')
        person = self.get_current_user()
        print("CommandHandler, person: {0}".format(person))
        result_object = {"reason":None, "code":200, "data":None}
        if not person:
            result_object['reason'] = 'Not Authenticated with Webex.'
            result_object['code'] = 401
        else:
            person = json.loads(person)
            #user = self.application.settings['db'].get_user(person['id'])
            if not self.is_allowed(person): #and user == None:
                result_object['reason'] = 'Not Authenticated.'
                result_object['code'] = 403
            elif command not in ['call_status', 'device_status', 'list_devices', 'list_cameras', 'move_camera', 'set_main_video_source', 'set_mute', 'set_volume', 'start_meeting']:
                result_object['reason'] = "{0} command not recognized.".format(command)
                result_object['code'] = 400
            else:
                result = None
                try:
                    if command == 'start_meeting':
                        success, data = yield self.start_meeting(person)
                        if not success:
                            result_object.update(data)
                        else:
                            result = data
                    elif command == 'list_devices':
                        result = yield self.list_devices()
                    else:
                        if(jbody.get("device_id")):
                            if command == 'call_status':
                                result = yield self.call_status(jbody)
                            elif command == 'device_status':
                                result = yield self.list_cameras(jbody)
                                microphones = yield self.mute_status(jbody)
                                volume = yield self.volume_status(jbody)
                                result.update({"microphones":microphones, "volume":volume})
                            elif command == 'list_cameras':
                                result = yield self.list_cameras(jbody)
                            elif command == 'move_camera':
                                result = yield self.move_camera(jbody)
                            elif command == 'set_main_video_source':
                                result = yield self.set_main_video_source(jbody)
                            elif command == 'set_mute':
                                result = yield self.set_mute(jbody)
                            elif command == 'set_volume':
                                result = yield self.set_volume(jbody)
                        else:
                            result_object['reason'] = "Missing required json parameter, 'device_id'"
                            result_object['code'] = 400
                except HTTPError as he:
                    traceback.print_exc()
                    result_object['reason'] = he.response.reason
                    result_object['code'] = he.code
                if result != None:
                    result_object["data"] = result
        res_val = json.dumps(result_object)
        print(res_val)
        self.write(res_val)


    @tornado.gen.coroutine
    def list_devices(self):
        devices_resp = yield DeviceBot.spark.get_with_retries_v2("https://webexapis.com/v1/devices")
        print("list_devices - devices_resp:{0}".format(devices_resp.body))
        devices = {}
        for item in devices_resp.body.get('items',[]):
            devices.update({ item['id'] : { "sip":item.get('primarySipUrl', item.get('sipUrls',[None])[0]), "name":item.get('displayName') }})
        raise tornado.gen.Return(devices)

    @tornado.gen.coroutine
    def start_meeting(self, person):
        success = False
        result = {'reason':"Unable to Encrypt Data", 'code':400}
        userSpark = Spark(person["token"])
        jose_url = 'https://mtg-broker-a.wbx2.com/api/v1/joseencrypt'
        payload = { "aud": Settings.aud, "jwt": {"sub": person["id"]} }
        jose_resp = yield userSpark.post_with_retries(jose_url, payload)
        print("start_meeting - jose_resp:{0}".format(jose_resp.body))
        host_data = jose_resp.body.get("host", [None])[0]
        print("start_meeting - host_data:{0}".format(host_data))
        mtg_url = 'https://mtg-broker-a.wbx2.com/api/v1/space/?int=jose&data='
        if host_data != None:
            mtg_url += host_data
            mtg_resp = yield userSpark.post_with_retries(mtg_url, allow_nonstandard_methods=True)
            print("start_meeting - mtg_resp:{0}".format(mtg_resp.body))
            conversation_id = None
            try:
                conversation_id = base64.b64decode(mtg_resp.body.get("spaceId")).decode('utf-8')
                conversation_id = conversation_id.split('/ROOM/')[1].strip()
            except Exception as e:
                traceback.print_exc()
            talk_url = 'https://instant.webex.com/hc/v1/talk?int=jose&v=1&data='
            result = {"url" :talk_url + host_data, "conversationId": conversation_id}
            success = True
        raise tornado.gen.Return((success, result))


    @tornado.gen.coroutine
    def call_status(self, jbody):
        url = "https://webexapis.com/v1/xapi/status?deviceId={0}&name=Call[0..100].Status".format(jbody.get("device_id"))
        call_resp = yield DeviceBot.spark.get_with_retries_v2(url)
        print("call_status - call_resp:{0}".format(call_resp.body))
        result = call_resp.body.get("result",{}).get("Call",[])
        raise tornado.gen.Return(result)
    
    @tornado.gen.coroutine
    def mute_status(self, jbody):
        url = "https://webexapis.com/v1/xapi/status?deviceId={0}&name=Audio.Input.Connectors.Microphone[0..10].Mute".format(jbody.get("device_id"))
        mute_resp = yield DeviceBot.spark.get_with_retries_v2(url)
        print("mute_status - mute_resp:{0}".format(mute_resp.body))
        result = mute_resp.body.get("result",{}).get("Audio",{}).get("Input",{}).get("Connectors",{}).get("Microphone",[])
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def volume_status(self, jbody):
        url = "https://webexapis.com/v1/xapi/status?deviceId={0}&name=Audio.Volume".format(jbody.get("device_id"))
        vol_resp = yield DeviceBot.spark.get_with_retries_v2(url)
        print("volume_status - vol_resp:{0}".format(vol_resp.body))
        result = vol_resp.body.get("result",{}).get("Audio",{}).get("Volume")
        raise tornado.gen.Return(result)


    @tornado.gen.coroutine
    def get_main_video_source(self, device_id):
        #main_source = "1"
        url = "https://webexapis.com/v1/xapi/status?deviceId={0}&name=Video.Input.MainVideoSource".format(device_id)
        source_resp = yield DeviceBot.spark.get_with_retries_v2(url)
        print("get_main_video_source - source_resp:{0}".format(source_resp.body))
        main_source = source_resp.body.get("result",{}).get("Video",{}).get("Input",{}).get("MainVideoSource", "1")
        raise tornado.gen.Return(main_source)

    @tornado.gen.coroutine
    def set_main_video_source(self, command_object):
        url = 'https://webexapis.com/v1/xapi/command/Video.Input.SetMainVideoSource'
        payload = {
            "deviceId":command_object["device_id"], 
            "arguments":{
                "SourceId": [command_object["source_id"]]
            }
        }
        source_resp = yield DeviceBot.spark.post_with_retries(url, payload)
        print("set_main_video_source - source_resp:{0}".format(source_resp.body))
        raise tornado.gen.Return(True)

    @tornado.gen.coroutine
    def list_cameras(self, jbody):
        url = "https://webexapis.com/v1/xapi/status?deviceId={0}&name=Cameras.Camera[0..100].Connected".format(jbody.get("device_id"))
        cameras_resp = yield DeviceBot.spark.get_with_retries_v2(url)
        print("list_cameras - cameras_resp:{0}".format(cameras_resp.body))
        cameras = cameras_resp.body.get("result",{}).get("Cameras",{}).get("Camera",[])
        main_video_source = yield self.get_main_video_source(jbody.get("device_id"))
        raise tornado.gen.Return({"cameras":cameras, "source":main_video_source})


    @tornado.gen.coroutine
    def get_position(self, device_id, camera_id, movement):
        base_get_url = 'https://webexapis.com/v1/xapi/status?deviceId={0}&name='.format(device_id)
        move_resp = yield DeviceBot.spark.get_with_retries_v2(base_get_url + 'Cameras.Camera[{0}].Position.{1}'.format(camera_id, movement))
        print("get_position - move_resp:{0}".format(move_resp.body))
        position = move_resp.body.get("result", {}).get("Cameras", {}).get("Camera", [{}])[0].get("Position", {})
        raise tornado.gen.Return(position)

    @tornado.gen.coroutine
    def move_camera(self, command_object):
        url = 'https://webexapis.com/v1/xapi/command/Camera.PositionSet'
        payload = {
            "deviceId":command_object["device_id"], 
            "arguments":{
                "CameraId": command_object["camera_id"]
            }
        }
        if(command_object["direction"] in ["left", "right"]):
            position = yield self.get_position(command_object["device_id"], command_object["camera_id"], "Pan")
            if(command_object["direction"] == "left"):
                adjustment = position.get("Pan",0) + 1000
            else:
                adjustment = position.get("Pan",0) - 1000
            direction_dict = {"Pan": adjustment}
        elif(command_object["direction"] in ["up", "down"]):
            position = yield self.get_position(command_object["device_id"], command_object["camera_id"], "Tilt")
            if(command_object["direction"] == "up"):
                adjustment = position.get("Tilt",0) + 1000
            else:
                adjustment = position.get("Tilt",0) - 1000
            direction_dict = {"Tilt": adjustment}
        elif(command_object["direction"] in ["in", "out"]):
            position = yield self.get_position(command_object["device_id"], command_object["camera_id"], "Zoom")
            if(command_object["direction"] == "in"):
                adjustment = position.get("Zoom",0) + 1000
            else:
                adjustment = position.get("Zoom",0) - 1000
            direction_dict = {"Zoom": adjustment}
        payload["arguments"].update(direction_dict)
        camera_resp = yield DeviceBot.spark.post_with_retries(url, payload)
        print("move_camera - camera_resp:{0}".format(camera_resp.body))
        raise tornado.gen.Return(direction_dict)

    @tornado.gen.coroutine
    def set_mute(self, command_object):
        url = 'https://webexapis.com/v1/xapi/command/Audio.Microphones.{0}'
        payload = {
            "deviceId":command_object["device_id"]
        }
        state = "Unmute"
        if(command_object["mute"]):
            state = "Mute"
        mute_resp = yield DeviceBot.spark.post_with_retries(url.format(state), payload)
        print("set_mute - mute_resp:{0}".format(mute_resp.body))
        raise tornado.gen.Return(True)

    @tornado.gen.coroutine
    def set_volume(self, command_object):
        url = 'https://webexapis.com/v1/xapi/command/Audio.Volume.Set'
        payload = {
            "deviceId":command_object["device_id"], 
            "arguments":{
                "Level": command_object["volume"]
            }
        }
        vol_resp = yield DeviceBot.spark.post_with_retries(url, payload)
        print("set_volume - vol_resp:{0}".format(vol_resp.body))
        raise tornado.gen.Return(True)



@tornado.gen.coroutine
def main():
    try:
        parse_command_line()
        app = tornado.web.Application([
                (r"/", MainHandler),
                (r"/command", CommandHandler),
                (r"/webex-oauth", WebexOAuthHandler),
                (r"/authentication-failed", AuthFailedHandler)
              ],
            template_path=os.path.join(os.path.dirname(__file__), "html_templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret="mcvmbnf4725mfbkjiashuduyebd",
            xsrf_cookies=False,
            debug=options.debug,
            )
        #db = UserDB.db
        #app.settings['db'] = db
        #expireAfterSeconds:0 actually means that the document will expire at the datetime specified by expire_date
        #db.msft_users.create_index("expire_date", expireAfterSeconds=0)
        #db.zoom_users.create_index("expire_date", expireAfterSeconds=0)
        #db.meetings.create_index([("person_id", ASCENDING), ("source_meeting_id", ASCENDING)], unique=True)
        server = tornado.httpserver.HTTPServer(app)
        server.bind(Settings.port)
        print("main - Serving... on port {0}".format(Settings.port))
        server.start()
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    main()
