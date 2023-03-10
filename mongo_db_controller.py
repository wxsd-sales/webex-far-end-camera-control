import copy
import traceback

from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError

from datetime import datetime, timedelta

from settings import Settings

class MongoController(object):
    def __init__(self):
        self.client = MongoClient(Settings.mongo_uri)
        self.db = self.client[Settings.mongo_db]
        self.meetings = self.db['meetings']
        self.zoom_users = self.db["zoom_users"]
        self.msft_users = self.db["msft_users"]
        self.meeting_types = {1:"Instant Meeting",
                              2:"Scheduled Meeting",
                              3:"Recurring meeting with no fixed time.",
                              4:"PMI Meeting",
                              8:"Recurring meeting with a fixed time."}

    def count(self):
        return self.zoom_users.estimated_document_count()

    def find(self, args):
        return self.zoom_users.find(args)

    def find_one(self, args):
        return self.unescape(self.zoom_users.find_one(args))

    def sanitize(self, mystr):
        return mystr.replace("~", "~e").replace(".", "~p").replace("$", "~d")

    def desanitize(self, mystr):
        return mystr.replace("~d", "$").replace("~p", ".").replace("~e", "~")

    def escape(self, document):
        document = copy.deepcopy(document)
        for q in dict(document['questions']):
            old_doc = document["questions"].pop(q)
            new_q = self.sanitize(q)
            for a in dict(old_doc):
                old_a = old_doc.pop(a)
                new_a = self.sanitize(a)
                old_doc.update({new_a:old_a})
            document['questions'].update({new_q: old_doc})
        return document

    def unescape(self, document):
        if document != None:
            for q in dict(document['questions']):
                old_doc = document["questions"].pop(q)
                new_q = self.desanitize(q)
                for a in dict(old_doc):
                    old_a = old_doc.pop(a)
                    new_a = self.desanitize(a)
                    old_doc.update({new_a:old_a})
                document['questions'].update({new_q: old_doc})
        return document

    def insert_user(self, person_id, token, expires_in, refresh_token, where="zoom"):
        result = None
        try:
            hours = 3600 * 8
            document = {
                        "person_id":person_id,
                        "token":token,
                        "expire_date":datetime.utcnow() + timedelta(seconds=expires_in+hours),
                        "refresh_token":refresh_token
            }
            mycol = self.db["{0}_users".format(where)]
            inserted = mycol.update_one({"person_id":person_id}, {"$set": document}, upsert=True)
            result = document
        except Exception as e:
            traceback.print_exc()
        return result

    def get_zoom_tokens(self, person_id):
        token = None
        refresh_token = None
        user = self.zoom_users.find_one({"person_id":person_id})
        if user != None:
            token = user.get('token')
            refresh_token = user.get('refresh_token')
        return token, refresh_token

    def is_user(self, person_id, where="zoom"):
        user = self.get_user(person_id, where)
        if user != None:
            user = True
        return user
        
    def get_user(self, person_id, where="zoom"):
        return self.db["{0}_users".format(where)].find_one({"person_id":person_id})

    def update_user(self, person_id, update_payload, where="msft"):
        self.db["{0}_users".format(where)].update_one({"person_id":person_id}, {"$set":update_payload})

    def delete_user(self, person_id, where="zoom"):
        self.db["{0}_users".format(where)].delete_one({"person_id":person_id})

    def find_meeting(self, meeting_id, person_id, alt_meeting_id=None):
        applicable_meeting_ids = [meeting_id]
        if alt_meeting_id != None:
            applicable_meeting_ids.append(alt_meeting_id)
        return self.meetings.find_one({"person_id": person_id, "$or" : [ {"source_meeting_id": {"$in": applicable_meeting_ids}} , {"alt_meeting_id": {"$in": applicable_meeting_ids}} ] })

    def insert_meeting(self, person_id, person_email, source_meeting_id, webex_meeting_id, alt_meeting_id=None):
        ret_val = False
        try:
            document = {"person_id":person_id,
                        "person_email":person_email,
                        "webex_meeting_id":webex_meeting_id,
                        "source_meeting_id":source_meeting_id}
            if alt_meeting_id not in [None, webex_meeting_id]:
                document.update({"alt_meeting_id":alt_meeting_id})
            self.meetings.insert_one(document)
            ret_val = True
        except DuplicateKeyError as dke:
            pass
        return ret_val

    def update(self, room_id, person_id, question, answers, anon, person_name, responded_users_type, prev_vote):
        question = self.sanitize(question)
        query = {"room_id":room_id}
        responded_users = "questions.{0}.responded_users".format(question)
        if responded_users_type == list:#this is to support an older version.  Can probably default to else in the future.
            update = { "$addToSet" : { responded_users : person_id }, "$inc": {} }
        else:
            update = { "$set" : { responded_users+"."+person_id: answers }, "$inc": {} }
        if anon is False:
            update.pop("$inc")
            update.update({"$push": {} })
            update.update({"$pull": {} })
        for answer in answers:
            if answer in prev_vote:
                prev_vote.remove(answer)
                continue
            answer = self.sanitize(answer)
            choice = "questions.{0}.{1}".format(question, answer)
            if anon is False:
                update["$push"].update({choice: person_name})
            else:
                update["$inc"].update({choice:1})
        for answer in prev_vote:
            answer = self.sanitize(answer)
            choice = "questions.{0}.{1}".format(question, answer)
            if anon is False:
                update["$pull"].update({choice: person_name})
            else:
                update["$inc"].update({choice:-1})
        if "$pull" in update and len(update["$pull"]) == 0:
            update.pop("$pull")
        if "$push" in update and len(update["$push"]) == 0:
            update.pop("$push")
        result = self.zoom_users.find_one_and_update(query, update, return_document=ReturnDocument.AFTER)
        return result


    def update_duration(self, room_id, duration):
        query = {"room_id":room_id}
        poll = self.zoom_users.find_one(query)
        old_duration = poll.get('duration')
        old_date = poll.get('end_date')
        new_date = poll.get('end_date') - timedelta(minutes=old_duration) + timedelta(minutes=int(duration))
        update = {"$set" : { "duration" : int(duration), "end_date" : new_date} }
        result = self.zoom_users.find_one_and_update(query, update, return_document=ReturnDocument.AFTER)
        print("mongo_db_controller update_duration result:{0}".format(result))
        msg = ""
        if result == None:
            msg = "There is currently no active poll in this space.  \n"
        else:
            msg = "Duration is now {0} minutes. Updated end date is now {1}  \n".format(result.get('duration'), result.get('end_date'))
        return msg

    def delete_one(self, query):
        deleted_count = 0
        try:
            x = self.zoom_users.delete_one(query)
            deleted_count = x.deleted_count
        except Exception as e:
            traceback.print_exc()
        return deleted_count


class UserDB(object):
    db = MongoController()
