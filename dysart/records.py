import datetime as dt
import functools
import hashlib
import json

import mongoengine as me


class RequestRecord(me.Document):
    """An unwrapped API request, to be persisted.

    Todo:
        Cookies? I'm not sure how to persist a MultiDict
    """

    UUID_LEN = 40

    time = me.DateTimeField()
    remote = me.StringField(max_length=39)  # max. length of ipv6 addr.
    path = me.StringField(max_length=80)
    text = me.StringField(required=False)  # DictField can't handle much
    response = me.StringField(required=False)

    def __init__(self, *args, **kwargs):
        """

        Args:
            request: An aiohttp request
        """
        super().__init__(*args, **kwargs)
        self.time = dt.datetime.now()
        self.__gen_uuid()
        self.save()

    @functools.cached_property
    def json(self):
        return json.loads(self.text)

    def __gen_uuid(self):
        """Creates a unique ID for the call record and assigned.

        Note that I am not using a hash function instead of the `uuid` module
        from the standard library because we specifically want a pseudorandom
        string with non-predictable values even in the most significant digits
        """
        h = hashlib.sha1(str(self.time).encode('utf-8'))
        h.update(self.remote.encode('utf-8'))
        self.uuid = h.hexdigest()[:RequestRecord.UUID_LEN]
