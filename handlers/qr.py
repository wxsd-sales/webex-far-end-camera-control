import base64
import json
import traceback
#import urllib.parse

import tornado.gen
import tornado.web

from base64 import b64encode
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError

from handlers.base import BaseHandler

from spark import Spark
from settings import Settings

class QRHandler(BaseHandler):

    @tornado.gen.coroutine
    def build_post(self, url, payload, headers={}):
        headers.update({
            'cache-control': "no-cache",
            'content-type': "application/x-www-form-urlencoded"
            })
        request = HTTPRequest(url, method="POST", headers=headers, body=payload)
        http_client = AsyncHTTPClient()
        response = yield http_client.fetch(request)
        raise tornado.gen.Return(response)

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        resp = {"success":False}
        try:
            jbody = json.loads(self.request.body)
            command = jbody.get('command')
            if command == "authorize":
                url = "https://webexapis.com/v1/device/authorize"
                payload = "client_id={0}&".format(Settings.webex_client_id)
                payload += "scope={0}".format(self.unencoded_scopes())
                response = yield self.build_post(url, payload)
                res = json.loads(response.body.decode("utf-8"))
                resp = {"success":True, "data":res}
                print("QRHandler.post /authorize response: {0}".format(resp))
            elif command == "poll":
                device_code = jbody.get('device_code')
                if device_code:
                    url = "https://webexapis.com/v1/device/token"
                    cred_str = "{0}:{1}".format(Settings.webex_client_id, Settings.webex_client_secret)
                    creds = base64.b64encode(cred_str.encode('utf-8')).decode('ascii')
                    headers = {"Authorization" : "Basic {0}".format(creds)}
                    payload = "grant_type=urn:ietf:params:oauth:grant-type:device_code&"
                    payload += "device_code={0}&".format(device_code)
                    payload += "client_id={0}".format(Settings.webex_client_id)
                    print(payload)
                    try:
                        response = yield self.build_post(url, payload, headers)
                        jresp = json.loads(response.body.decode("utf-8"))
                        resp = {"success":True, "data":jresp}
                        print("QRHandler.post /token response: {0}".format(resp))
                    except HTTPError as he:
                        print("QRHandler.post /token Error Code:{0}".format(he.code))
                        if(he.code != 428):
                            try:
                                print(he.response.body)
                            except Exception as ex:
                                pass
                        resp['reason'] = he.response.reason
                else:
                    resp.update({"reason":"'poll' command requires parameter 'device_code'."})
            else:
                resp.update({"reason":"required parameter 'command' missing or unrecognized."})
        except Exception as e:
            print("QRHandler.post Exception:{0}".format(e))
            traceback.print_exc()
        self.write(json.dumps(resp))

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        person = self.get_current_user()
        if not person:
            #resp = yield self.get_qr_code()
            self.render("qr.html")
        else:
            self.load_main_page(person)