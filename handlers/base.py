import json
import tornado.web
from settings import Settings

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        cookie = self.get_secure_cookie(Settings.cookie_user, max_age_days=1, min_version=2)
        return cookie

    def load_page(self, page="index"):
        redirect_to = ""
        if page != "index":
            redirect_to += "?state={0}".format(page)
        person = self.get_current_user()
        if not person:
            self.redirect('/webex-oauth{0}'.format(redirect_to))
        else:
            person = json.loads(person)
            print(person)
            #tokens = {"token":self.application.settings['db'].is_user(person['id'])}
            self.render("{0}.html".format(page), person=person)
