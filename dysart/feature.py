"""
Top-level DySART feature class. Defines dependency-solving behavior at a high
level of abstraction, deferring implementation of update conditions to user-
defined subclasses.

The Feature interface is designed to be as nearly invisible as possible. The
rationale goes like this: someone---somewhere, somewhen---has to explicitly
specify the device-property dependency graph. This person (the "user") should be
protected only from thinking about more than one system layer _at a time_.
Later on, some other scientist might like to take a far-downstream measurement
without having to think about _anything_ more than the highest leayer of
"""

import datetime as dt
from enum import Enum
from functools import wraps
import getpass
import hashlib
import socket
import sys
import time

from mongoengine import *

import dysart.messages.messages as messages

CALLRECORD_UID_LEN = 40

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
    class's update mthod, to return these two values.

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
        with CallRecord(feature=feature,
                        method=fn.__name__,
                        initiating_call=initiating_call,
                        stack_level=stack_level,
                        user=getpass.getuser(),
                        hostname=socket.gethostname()) as record:


            # is_stale tracks whether we need to update this node
            is_stale = False
            # if this call recurses, recurse on ancestors.
            if feature.is_recursive():
                for parent_key in feature.parents:
                    # Call parent to refresh recursively; increment stack depth
                    parent_is_stale = feature.parents[parent_key]\
                                    .touch(initiating_call=record, is_stale=0)
                    is_stale |= parent_is_stale
            # If stale for some other reason, also flag to be updated.
            feature_expired = feature._expired(call_record=None)
            is_stale |= feature_expired
            is_stale |= feature.manual_expiration_switch
            # If this line is in a later place, __call__ is called twice. You need
            # to understand why.
            feature.manual_expiration_switch = False
            # Call the update-self method, the reason for this wrapper's existence
            if is_stale:
                feature(initiating_call=initiating_call)
            # Update staleness parameter in case it was passed in with the function
            # TODO: this currently only exists for the benefit of Feature.touch().
            # If that method is removed, consider getting rid of this snippet, too.
            if 'is_stale' in kwargs:
                kwargs['is_stale'] = is_stale

            # Call the requested function!
            return_value = fn(*args, **kwargs)
            # Save any changes to the database
            # feature.manual_expiration_switch = False
            feature.save()

        # this_call.save()

        # Finally, pass along return value of fn
        return return_value
    wrapped_fn.is_refresh = True
    return wrapped_fn


class Feature(Document):
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
    name = StringField(default='', required=True, primary_key=True)
    manual_expiration_switch = BooleanField(default=False)
    is_stale_func = StringField(max_length=60)
    refresh_func = StringField(max_length=60)
    parents = DictField(default={})

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
        s = ''
        # Initialize as object name with type judgment
        if self._expired():
            s = messages.cstr(self.name, 'fail')
        else:
            s = messages.cstr(self.name, 'ok')
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
        print(messages.tree(self, lambda obj: obj.parents.values()))

    def _properties(self):
        """
        TODO real get_properties docstring
        Return a list of all the refresh methods of the feature
        """
        class_dict = self.__class__.__dict__
        return [p for p in class_dict if hasattr(class_dict[p], 'is_refresh') and
                not p.startswith('_')]  # ignore self._collections

    @property
    def properties(self):
        """
        TODO real properties docstring
        Pretty-print a human-readable description of all the object's property
        methods
        """
        class_dict = self.__class__.__dict__
        print('')
        for prop in self._properties():
            messages.pprint_func(prop, self.__class__.__dict__[prop].__doc__)

    def _call_records(self) -> list:
        """Return a list of CallRecords associated with this Feature
        """
        return CallRecord.objects(feature=self)

    def call_records(self) -> list:
        """Pretty-print a list of CallRecords associated with this Feature
        """
        for record in self._call_records():
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

    def _expired(self, call_record=None) -> bool:
        """Check for feature expiration. By default, everything is a twinkie.
        """

        return self.manual_expiration_switch

    def set_expired(self, is_expired: bool = True) -> None:
        """Provide an interface to manually set the expiration state of a feature.
        """
        self.manual_expiration_switch = is_expired
        self.save()

    def update(self):
        pass

    def is_recursive(self) -> bool:
        """Does dependency-checking recurse on this feature? By default, yes.
        Even though this does nothing now, I'm leaving it here to indicate that
        a feature might take its place in the future.
        """
        return True

    def add_parents(self, *new_parents) -> bool:
        """Insert a dependency into the feature's parents list and write to the
        database. Can pass a single feature, multiple features as
        comma-separated parameters, a list of features, a list of list of
        features, and so on.
        """
        for parent in new_parents:
            # Handle (arbitrarily deeply nested) lists of parents.
            # This works with explicit type-checking, but it's not the most
            # pythonic solution in the world. Could be done more canonically
            # Feature weren't iterable!
            if isinstance(parent, Feature):
                if parent not in self.parents:
                    print("ok, adding a parent!")
                    self.parents.append(parent)
            else:
                self.add_parents(*parent)
        self.save()


class CallRecord(Document):
    """
    TODO CallRecord docstring

    Uniquely identified (with high probability) by a 40-character hexadecimal
    string.
    """

    meta = {'allow_inheritance': True}

    # Exit codes
    DONE = 'DONE'
    FAILED = 'FAILED'
    WARNING = 'WARNING'

    # Which attributes are included in self.__str__()?
    printed_attrs = ['feature',
                     'method',
                     'start_time',
                     'stop_time',
                     'user',
                     'hostname',
                     'exit_status',]

    initiating_call = ReferenceField('self', null=True)
    stack_level = IntField(default=0)
    feature = ReferenceField(Feature, required=True)
    method = StringField(max_length=80)
    uid = StringField(default='', max_length=CALLRECORD_UID_LEN, required=True, primary_key=True)
    start_time = DateTimeField()
    stop_time = DateTimeField()
    user = StringField(max_length=255)
    hostname = StringField(max_length=255)
    exit_status = StringField(max_length=40, default='DONE')
    info = StringField(default='')

    def __init__(self, *args, **kwargs):
        """To create a CallRecord, should receive `feature` and `initiating_call`
        args
        """
        super().__init__(*args, **kwargs)

        # TODO
        # Check if this is a recovery

        # Generate a uid
        # TODO maybe this should be a hash of the called feature's state
        h = hashlib.sha1(self.feature.name.encode('utf-8'))
        h.update(str(self.start_time).encode('utf-8'))
        if self.initiating_call:
            h.update(self.initiating_call.uid.encode('utf-8'))
        self.uid = h.hexdigest()[:CALLRECORD_UID_LEN]

        self.save()

    def __enter__(self):
        """Note use of CallRecord as a context manager for refresh function.
        Redirects stdout: but note inheriting from contextlib.redirect_stdout
        causes a metaclass conflict.
        """
        self.__old_stdout = sys.stdout
        sys.stdout = self
        self.start_time = dt.datetime.now()
        self.save()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_time = dt.datetime.now()
        if exc_type is not None:
            self.exit_status = '{}: {}'.format(CallRecord.FAILED, exc_value)
        else:
            self.exit_status = CallRecord.DONE

        sys.stdout = self.__old_stdout
        self.save()

    def write(self, data: str):
        """TODO docstring
        """
        self.info += data

    def flush(self):
        """TODO docstring
        """
        pass

    def __str__(self):
        s = self.uid[:16] + '...\n'
        for attr in CallRecord.printed_attrs:
            max_attr_len = max(map(len, CallRecord.printed_attrs))
            val = getattr(self, attr)
            if isinstance(val, Feature):
                val = val.name
            s += ' ' + messages.cstr(attr, 'italic') + ' ' * (max_attr_len - len(attr))\
                    + ' : {}\n'.format(val)
        return s

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
