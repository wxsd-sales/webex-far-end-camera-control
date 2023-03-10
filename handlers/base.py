import json
import traceback
import tornado.gen
import tornado.web
import urllib.parse
from settings import Settings
from spark import Spark

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        person = self.get_secure_cookie(Settings.cookie_user, max_age_days=1, min_version=2)
        token = self.get_secure_cookie(Settings.cookie_user_token, max_age_days=1, min_version=2)
        if type(token) == bytes:
            token = token.decode('utf-8')
        if person:
            person = json.loads(person)
            person.update({"token":token})
        return person

    def save_current_user(self, person, token):
        self.set_secure_cookie(Settings.cookie_user, json.dumps(person.body), expires_days=1, version=2)
        self.set_secure_cookie(Settings.cookie_user_token, token, expires_days=1, version=2)
    
    def delete_current_user(self):
        self.clear_cookie(Settings.cookie_user)
        self.clear_cookie(Settings.cookie_user_token)
    
    def unencoded_scopes(self):
        return Settings.webex_scopes.replace("%20", " ").replace("%3A", ":")

    def load_main_page(self, person):
        print(person)
        #tokens = {"token":self.application.settings['db'].is_user(person['id'])}
        self.render("index.html", person=person)

    def load_page(self, state=""):
        try:
            person = self.get_current_user()
            print('load_page person:{0}'.format(person))
            if not person:
                args = ""
                if state != "":
                    state = urllib.parse.quote_plus(state)
                    print('url encoded state:{0}'.format(state))
                    args = '?state={0}'.format(state)
                self.redirect('/webex-oauth{0}'.format(args))
            else:
                self.load_main_page(person)
        except Exception as e:
            traceback.print_exc()
    
    def is_allowed(self, person):
        is_org_user = person["orgId"] == Settings.org_id
        is_allowed_user = person.get("emails", [None])[0] in Settings.users
        return is_org_user or is_allowed_user

    def redirect_page(self, redirect_path):
        for arg in self.request.arguments:
            if arg not in ["returnTo", "token"]:
                arg_val = self.request.arguments[arg][0].decode('utf-8')
                if arg_val != "":
                    redirect_path += '{0}={1}&'.format(arg, arg_val)
        self.redirect(redirect_path)
