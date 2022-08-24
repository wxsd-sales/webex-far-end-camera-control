import json
import tornado.web
import urllib.parse
from settings import Settings

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        cookie = self.get_secure_cookie(Settings.cookie_user, max_age_days=1, min_version=2)
        return cookie

    def load_page(self, page="index", state=""):
        person = self.get_current_user()
        if not person:
            args = ""
            if state != "":
                state = urllib.parse.quote_plus(state)
                print('url encoded state:{0}'.format(state))
                args = '?state={0}'.format(state)
            self.redirect('/webex-oauth{0}'.format(args))
        else:
            person = json.loads(person)
            print(person)
            #tokens = {"token":self.application.settings['db'].is_user(person['id'])}
            self.render("{0}.html".format(page), person=person)
    
    def is_allowed(self, person):
        is_org_user = person["orgId"] == Settings.org_id
        is_allowed_user = person.get("emails", [None])[0] in Settings.users
        return is_org_user or is_allowed_user
