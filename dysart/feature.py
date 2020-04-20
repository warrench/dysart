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
from functools import wraps
import getpass
import hashlib
import socket
import sys
from typing import *

import mongoengine as me

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
        with CallRecord(feature=feature,
                        method=fn.__name__,
                        initiating_call=initiating_call,
                        stack_level=stack_level,
                        user=getpass.getuser(),
                        hostname=socket.gethostname()) as record:

            # First run the optional pre-hook, if any
            pre_hook = getattr(feature, '__pre_hook__', None)
            if pre_hook is not None:
                pre_hook(record)

            # is_stale tracks whether we need to update this node
            is_stale = False
            # if this call recurses, recurse on ancestors.
            if feature.is_recursive():
                for parent in feature.parents.values():
                    # Call parent to refresh recursively; increment stack depth
                    parent_is_stale = parent.touch(initiating_call=record, is_stale=0)
                    is_stale |= parent_is_stale
            # If stale for some other reason, also flag to be updated.
            is_stale |= feature.expired(call_record=None)
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
            
            # Finally, run the optional post-hook, if any
            post_hook = getattr(feature, '__post_hook__', None)
            if post_hook is not None:
                post_hook(record)

        # this_call.save()

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

    def call_records(self, **kwargs) -> list:
        """Return a list of CallRecords associated with this Feature.

        """
        try:
            return CallRecord.objects(feature=self, **kwargs)
        except me.errors.InvalidQueryError as e:
            # TODO: use a standard error-reporting method in the messages module.
            print("Invalid call record field: allowedfields are TODO", sys.stderr)

    def pprintt_call_records(self) -> list:
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


class CallRecord(me.Document):
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

    initiating_call = me.ReferenceField('self', null=True)
    stack_level = me.IntField(default=0)
    feature = me.ReferenceField(Feature, required=True)
    method = me.StringField(max_length=80)
    uid = me.StringField(default='', max_length=CALLRECORD_UID_LEN, required=True, primary_key=True)
    start_time = me.DateTimeField()
    stop_time = me.DateTimeField()
    user = me.StringField(max_length=255)
    hostname = me.StringField(max_length=255)
    exit_status = me.StringField(max_length=40, default='DONE')
    info = me.StringField(default='')

    def __init__(self, *args, **kwargs):
        """To create a CallRecord, should receive `feature` and `initiating_call`
        args
        """
        super().__init__(*args, **kwargs)

        # TODO
        # Check if this is a recovery

        # Generate a uid
        # TODO maybe this should be a hash of the called feature's state
        h = hashlib.sha1(self.feature.id.encode('utf-8'))
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
        # TODO I'm not really sure this should divert stdout.
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

        # TODO I'm not really sure this should divert stdout.
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
                val = val.id
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
