"""
Top-level DySART feature class. Defines dependency-solving behavior at a high
level of abstraction, deferring implementation of update conditions to user-
defined subclasses.

The Feature interface is designed to be as nearly invisible as possible. The
rationale goes like this: someone---somewhere, somewhen---has to explicitly
specify the device-property dependency graph. This person (the "user") should be
protected only from thinking about more than one system layer _at a time_.
Later on, some other scientist might like to take a far-downstream measurement
without having to think about _anything_ more than the highest layer defined by
the last person who touched the system.
"""

import datetime as dt
import enum
from functools import wraps
import getpass
import hashlib
import socket
import sys
from typing import *

import mongoengine as me

import dysart.messages.messages as messages


class ExpirationStatus(enum.Enum):
    FRESH = enum.auto()
    EXPIRED = enum.auto()


def refresh(fn):
    """Decorator that flags a method as having dependencies and possibly requiring
    a refresh operation. Recursively refreshes ancestors, then checks an
    additional condition `_expired()` specified by the Feature class. If the
    feature or its ancestors have expired, perform the corrective operation
    defined by the _______ method.

    An advantage of using a refresh decorator to solve the dependency problem
    is that a given feature may have a variety of public methods with the same
    dependencies. This situation can be illustrated by a QubitRabi feature with
    public methods `pi_time` and `pi_2_time` accessed as properties:

        @refresh
        def pi_time(self):
            return self.data['pi_time']

        @refresh
        def pi_2_time(self):
            return self.data['pi_2_time']

    If we access qubit_rabi.pi_time followed by qubit_rabi.pi_2_time, they
    should use the same measurement & fit results, from a single call to the
    class's update method, to return these two values.

    This is a pretty central feature, and it must be done right. This should be
    a focus of any future code review, so

    """
    @wraps(fn)
    def wrapped_fn(*args, **kwargs):
        """
        The modified function passed to refresh.
        """

        feature = args[0]

        # Generate new call record from initiating call record
        # Ensure that initiating_call is defined
        if 'initiating_call' in kwargs:
            initiating_call = kwargs['initiating_call']
            stack_level = initiating_call.stack_level + 1
        else:
            initiating_call = None
            stack_level = 0

        # And create the new call record.
        record = CallRecord(
            feature=feature,
            method=fn.__name__,
            initiating_call=initiating_call,
            stack_level=stack_level,
            user=getpass.getuser(),
            hostname=socket.gethostname()
        )
        record.setup()

        # First run the optional pre-hook, if any
        if hasattr(feature, '__pre_hook__'):
            feature.__pre_hook__(record)
            
        try:
            # Call the Feature--this is the reason for this wrapper's existence
            # TODO note that `is_stale` sounds like it just returns a boolean--
            # but it has very significant side-effects. This is probably a
            # symptom of poor design.
            is_stale = feature.is_stale(record)
            if is_stale:
                feature(initiating_call=initiating_call)
            # Update staleness parameter in case it was passed in with the function
            # TODO: this currently only exists for the benefit of Feature.touch().
            # That is *so* complex and unintuitive. What spaghetti code.
            # If that method is removed, consider getting rid of this snippet, too.
            if 'is_stale' in kwargs:
                kwargs['is_stale'] = is_stale
            # Call the requested function!
            return_value = fn(*args, **kwargs)
            
            # Run the optional validation hook, if any 
            if hasattr(feature, '__validation_hook__'):
                feature.__validation_hook__(record, return_value)
            
            # Save any changes to the database
            # feature.manual_expiration_switch = False
            feature.save()
            status = CallStatus.DONE
        except Exception as e:
            status = CallStatus.FAILED
        finally:
            record.conclude(status)
            # Finally, run the optional post-hook, if any
            if hasattr(feature, '__post_hook__'):
                feature.__post_hook__(record)

        # Finally, pass along return value of fn
        return return_value
    
    wrapped_fn.is_refresh = True
    return wrapped_fn


class Feature(me.Document):
    """
    Device or component feature class. Each measurement should be implemented
    as an instance of this class.
    """

    call_message = 'updating feature'
    meta = {'allow_inheritance': True}

    # Feature payload. One of the drawbacks of using mongoengine is that the
    # structure of the payload is pretty constrained, and on top of that I
    # don't really know how it is represented in the database.
    # Hence "data" as a dict blob.
    id = me.StringField(default='', required=True, primary_key=True)
    manual_expiration_switch = me.BooleanField(default=False)
    is_stale_func = me.StringField(max_length=60)
    refresh_func = me.StringField(max_length=60)
    parent_ids = me.DictField(default={})

    def __init__(self, **kwargs):
        # Create a new document
        super().__init__(**kwargs)
        self.save()

    def _status(self) -> str:
        """
        returns a pretty-printed string containing detailed information about
        the feature's current status; e.g. the details of recently-found
        fitting parameters. Should be overridden by derived classes.
        """
        return ''

    def __str__(self):
        """should report its name, most-derived (?) type, parents, and names and
        expiration statuses thereof.
        """
        # Initialize as object name with type judgment
        if self.expired():
            s = messages.cstr('[EXP]', 'fail')
        else:
            s = messages.cstr('[OK]', 'ok')
        # Descriptor of this feature
        s += '\t: ' + messages.cstr(self.__class__.__name__, 'bold')
        # This feature's status
        status = self._status()
        if status:
            s += '\n' + status
        return s

    def tree(self) -> None:
        """Draw to the terminal a pretty-printed tree of all this Feature's
        dependents.
        """
        print(messages.tree(self, lambda obj: self.parents.values()))

    def _properties(self):
        """
        TODO real _properties docstring
        Return a list of all the refresh methods of the feature
        """
        class_dict = self.__class__.__dict__
        return [p for p in class_dict if hasattr(class_dict[p], 'is_refresh') and
                not p.startswith('_')]  # ignore self._collections

    def properties(self):
        """
        TODO real properties docstring
        TODO rename this; it may be confused with the property decorator
        Pretty-print a human-readable description of all the object's property
        methods
        """
        print('')
        for prop in self._properties():
            messages.pprint_func(prop, self.__class__.__dict__[prop].__doc__)

    def call_records(self, **kwargs) -> me.QuerySet:
        """Return a list of CallRecords associated with this Feature.

        """
        try:
            return CallRecord.objects(feature=self, **kwargs)
        except me.errors.InvalidQueryError as e:
            # TODO: use a standard error-reporting method in the messages module.
            print("Invalid call record field: allowedfields are TODO", sys.stderr)

    def pprint_call_records(self) -> list:
        """Pretty-print a list of CallRecords associated with this Feature
        """
        for record in self.call_records():
            print(record)

    def __call__(self, initiating_call=None, **kwargs):
        """Feature is callable. This method does whatever is needed to update an
        expired feature. By default, calling the instance only refreshes and
        logs. Unless overwritten, just updates the time-since-refresh and
        returns itself. This strikes me as a convenient expressionn of intent
        in some ways, but it's also a little unpythonic: "explicit is better
        than implicit".

        """
        return

    def is_stale(self, record):
        """A pretty weird internal method
        """
        is_stale = False
        # if this call recurses, recurse on ancestors.
        for parent in self.parents.values():
            # Call parent to refresh recursively; increment stack depth
            is_stale |= parent.touch(initiating_call=record, is_stale=False)
        # If stale for some other reason, also flag to be updated.
        is_stale |= self.expired(call_record=None)
        is_stale |= self.manual_expiration_switch
        # If this line is in a later place, __call__ is called twice. You need
        # to understand why.
        self.manual_expiration_switch = False
        return is_stale

    @refresh
    def touch(self, initiating_call=None, is_stale=False) -> bool:
        """Manually refresh the feature without doing anything else. This method has a
        special role, being invoked by DySART as the default refresh method
        called as it climbs the feature tree. It's also treated in a special
        way by @refresh, in order to propagate refresh data downstream. While
        this does work, it's a little bit unpythonic: "explicit is better than
        implicit". In short, this is a hack, and it shouldn't last.
        """
        return is_stale

    def expired(self, call_record: "CallRecord" = None) -> object:
        """Check for feature expiration.
        """
        expired = self.manual_expiration_switch
        if hasattr(self, '__expiration_hook__'):
            expired |= self.__expiration_hook__() == ExpirationStatus.EXPIRED
        return expired

    def set_expired(self, is_expired: bool = True) -> None:
        """Provide an interface to manually set the expiration state of a feature.
        """
        self.manual_expiration_switch = is_expired
        self.save()

    def update(self):
        pass

    @property
    def parents(self):
        """How parents should be accessed by clients. This property is a mapping
        from parent keys, which identify the relationship, purpose or intent of a
        parent object, to the corresponding parent objects.

        """
        return {key: self.__get_parent(key) for key in self.parent_ids}

    def __get_parent(self, parent_key):
        """Returns the parent associated with a parent key. This is an internal
        method used by the `parents` property.

        """
        parents = Feature.objects(id=self.parent_ids[parent_key])
        if len(parents) == 0:
            # TODO
            pass
        if len(parents) > 1:
            raise me.errors.MultipleObjectsReturned
        return parents[0]

    def add_parents(self, new_parents: Dict):
        """Insert dependencies into the feature's parents dictionary and
        write to the database.
        """
        for parent_key, parent_id in new_parents.items():
            self.parent_ids[parent_key] = parent_id
        self.save()


class CallStatus(enum.Enum):
    START = enum.auto()
    DONE = enum.auto()
    FAILED = enum.auto()
    HALTED = enum.auto()
    WARNING = enum.auto()


class CallRecord(me.Document):
    """
    TODO CallRecord docstring

    Uniquely identified (with high probability) by a 40-character hexadecimal
    string.
    """

    meta = {'allow_inheritance': True}

    UUID_LEN = 40

    # Which attributes are included in self.__str__()?
    printed_attrs = ['feature',
                     'method',
                     'start_time',
                     'stop_time',
                     'user',
                     'hostname',
                     'exit_status',]

    initiating_call = me.ReferenceField('self', null=True)
    stack_level = me.IntField(default=0)
    feature = me.ReferenceField(Feature, required=True)
    method = me.StringField(max_length=80)
    uuid = me.StringField(default='', max_length=UUID_LEN, required=True, primary_key=True)
    start_time = me.DateTimeField()
    stop_time = me.DateTimeField()
    user = me.StringField(max_length=255)
    hostname = me.StringField(max_length=255)
    exit_status = me.StringField(max_length=16)
    info = me.StringField(default='')

    def __init__(self, *args, **kwargs):
        """To create a CallRecord, should receive `feature` and `initiating_call`
        args
        """
        super().__init__(*args, **kwargs)
        
    def __setattr__(self, key, value):
        """The `exit_status` field should be a string, so handle this
        case in a special way: accept only CallStatus enums, but
        """
        if key == 'exit_status' and type(value) == CallStatus:
            super().__setattr__(key, value.name)
        else:
            super().__setattr__(key, value)

    def setup(self):
        """ This is run to setup the call record before the actual call is
        issued.
        
        Note that the contents of this method *cannot* go into init, as this
        causes a slightly subtle but disastrous bug that leads to exponential
        blowup in the number of CallRecords, as each time a record is accessed
        it forks once it receives a new uuid.
        """
        self.start_time = dt.datetime.now()
        self.__gen_uuid()
        self.save()
    
    def conclude(self, status: CallStatus):
        """ ...and this one tears it down
        """
        self.exit_status = status
        self.stop_time = dt.datetime.now()
        self.save()

    def __str__(self):
        s = self.uuid[:16] + '...\n'
        for attr in CallRecord.printed_attrs:
            max_attr_len = max(map(len, CallRecord.printed_attrs))
            val = getattr(self, attr)
            if isinstance(val, Feature):
                val = val.id
            s += ' ' + messages.cstr(attr, 'italic') + ' ' * (max_attr_len - len(attr))\
                     + ' : {}\n'.format(val)
        return s
    
    def __gen_uuid(self):
        """Creates a unique ID for the call record and assigned.
        
        Must be called after assigning a start time.
        
        Note that I am not using a hash function instead of the `uuid` module
        from the standard library because we specifically want a pseudorandom
        string with non-predictable values even in the most significant digits
        """
        h = hashlib.sha1(self.feature.id.encode('utf-8'))
        h.update(str(self.start_time).encode('utf-8'))
        if self.initiating_call:
            h.update(self.initiating_call.uuid.encode('utf-8'))
        self.uuid = h.hexdigest()[:CallRecord.UUID_LEN]

    def get_initiated_call(self, other_feature):
        # Should search tree for a matching call.
        return None

    def root_call(self) -> 'CallRecord':
        """Get the ultimate root of the call tree--this should be input from a user,
        cron daemon or similar.
        """
        if self.initiating_call == None:
            return self
        else:
            return self.initiating_call.root_call()


def get_records_by_uid_pre(uid_pre):
    """Takes a uid prefix and searches for a record whose uid contains this
    substring.
    """
    matches = CallRecord.objects(uid__istartswith=uid_pre)
    return matches


def get_records_by_uid_sub(uid_sub):
    """Takes a uid /sub/string and searches for a record whose uid contains this
    substring.
    """
    matches = CallRecord.objects(uid__icontains=uid_sub)
    return matches
