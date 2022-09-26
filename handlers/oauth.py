import json
import traceback
import urllib.parse

import tornado.gen
import tornado.web

from base64 import b64encode
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from handlers.base import BaseHandler

from spark import Spark
from settings import Settings

class WebexOAuthHandler(BaseHandler):

    def build_access_token_payload(self, code, client_id, client_secret, redirect_uri):
        payload = "client_id={0}&".format(client_id)
        payload += "client_secret={0}&".format(client_secret)
        payload += "grant_type=authorization_code&"
        payload += "code={0}&".format(code)
        payload += "redirect_uri={0}".format(redirect_uri)
        return payload

    @tornado.gen.coroutine
    def get_tokens(self, code):
        url = "https://webexapis.com/v1/access_token"
        payload = self.build_access_token_payload(code, Settings.webex_client_id, Settings.webex_client_secret, Settings.webex_redirect_uri)
        headers = {
            'cache-control': "no-cache",
            'content-type': "application/x-www-form-urlencoded"
            }
        success = False
        try:
            request = HTTPRequest(url, method="POST", headers=headers, body=payload)
            http_client = AsyncHTTPClient()
            response = yield http_client.fetch(request)
            resp = json.loads(response.body.decode("utf-8"))
            print("WebexOAuthHandler.get_tokens /access_token Response: {0}".format(resp))
            person = yield Spark(resp['access_token']).get_with_retries_v2('https://webexapis.com/v1/people/me')
            print("person.body:{0}".format(person.body))
            if not self.is_allowed(person.body):
                self.redirect('/authentication-failed')
            else:
                self.save_current_user(person, resp['access_token'])
                success = True
        except Exception as e:
            print("WebexOAuthHandler.get_tokens Exception:{0}".format(e))
            traceback.print_exc()
        raise tornado.gen.Return(success)



    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        response = "Error"
        try:
            print('Webex OAuth: {0}'.format(self.request.full_url()))
            state = self.get_argument("state","")
            person = self.get_current_user()
            print('Webex OAuth state:{0}'.format(state))
            if not person:
                if self.get_argument("code", None):
                    code = self.get_argument("code")
                    success = yield self.get_tokens(code)
                    if success:
                        state = urllib.parse.unquote_plus(state)
                        self.redirect("/"+state)
                    return
                else:
                    authorize_url = '{0}?client_id={1}&response_type=code&redirect_uri={2}&scope={3}&state={4}'
                    use_url = 'https://webexapis.com/v1/authorize'
                    authorize_url = authorize_url.format(use_url, Settings.webex_client_id, urllib.parse.quote_plus(Settings.webex_redirect_uri), Settings.webex_scopes, urllib.parse.quote_plus(state))
                    print("WebexOAuthHandler.get authorize_url:{0}".format(authorize_url))
                    self.redirect(authorize_url)
                    return
            else:
                print("Already authenticated.")
                self.redirect(state)
                return
        except Exception as e:
            response = "{0}".format(e)
            print("WebexOAuthHandler.get Exception:{0}".format(e))
            traceback.print_exc()
        self.write(response)
