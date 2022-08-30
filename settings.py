import os
from dotenv import load_dotenv

load_dotenv()

class Settings(object):
	port = int(os.environ.get("MY_APP_PORT"))
	cookie_user = os.environ.get("MY_COOKIE_USER")
	cookie_user_token = cookie_user + "-token"
	bot_token = os.environ.get("MY_BOT_TOKEN")
	aud = os.environ.get("MY_INSTANT_CONNECT_AUD")
	org_id = os.environ.get("MY_ORG_ID")
	users = os.environ.get("MY_USERS", [])
	if users != []:
		users = users.split(',')
	
	webex_client_id = os.environ.get("MY_WEBEX_CLIENT_ID")
	webex_client_secret = os.environ.get("MY_WEBEX_SECRET")
	webex_redirect_uri = os.environ.get("MY_WEBEX_REDIRECT_URI")
	webex_scopes = os.environ.get("MY_WEBEX_SCOPES")

	#mongo_uri = os.environ.get("MY_MONGO_URI")
	#mongo_db = os.environ.get("MY_MONGO_DB")
