from mongoengine import *
import datetime as dt
import getpass
import hashlib
from .feature import Feature

# Number of hexadecimal digits in a CallRecord uid.
uid_len = 40

class CallRecord(Document):
    """
    TODO CallRecord docstring

    Uniquely identified (with high probability) by a 40-character hexadecimal
    string.
    """
    
    uid_len = 40

    # Exit codes
    DONE = 'done'
    FAILED = 'failed'
    WARNING = 'warning'

    initiating_call = ReferenceField(CallRecord, default=None)
    level = IntField(default=0)
    feature = ReferenceField(Feature, required=True)
    uid = StringField(default='', max_length=uid_len, required=True, primary_key=True)
    timestamp = DateTimeField(default=dt.datetime.now())
    user = StringField(max_length=255)
    exit_status = StringField(max_length=40)

    def __init__(self, feature, initiating_call):
        self.initiating_call = initiating_call
        self.feature = feature
        self.timestamp = dt.datetime.now()
        if initiating_call == None:
            self.level = None
        else:
            self.level = initiating_call.level + 1
        
        # Generate a uid
        # TODO really this should be a hash of the called feature's state
        h = hashlib.sha1(str.encode(self.feature.name))
        if self.initiating_call == None:
            h.update(str.encode(str(self.timestamp)))
        else:
            h.update(self.initiating_call.uid)
        self.uid = h.hexdigest()[:uid_len]
        
        self.user =  getpass.getuser()

        self.save()

    def get_initiated_call(self, other_feature):
        # Should search tree for a matching call.
        return None



def get_records_by_uid(uid_sub):
    """
    TODO get_record docstring
    Takes a uid /sub/string and searches for a record whose uid contains this
    substring.
    """
    # Look for a library function for this. Is it possible to make a
    # mongoengine query for a fields satisfying a predicate?
    sub_len = len(uid_sub)
    matching_records = [record for record in CallRecord.objects\
                        if record.uid[:sub_len] == uid_sub]
    return matching_records

def get_record(uid_sub):
    """
    TODO get_record docstring
    As above, but raises an exception if more than one item is returned
    """
    matching_records = get_records_by_uid(uid_sub)
    if len(matching_records) > 1:
        raise MultipleObjectsReturned
    elif not matching_records:
        raise DoesNotExist
    return matching_records[0]
