"""
Top-level dysart feature class. Defines dependency-solving behavior at a high
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
import hashlib
import getpass
import time

from mongoengine import *

import dysart.messages.messages as messages


def refresh(fn):
    """
    Decorator that flags a method as having dependencies and possibly requiring
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
        else:
            initiating_call = None
        # And create the new call record.
        this_call = CallRecord(feature, initiating_call=initiating_call)

        # is_stale tracks whether we need to update this node
        is_stale = False
        # if this call recurses, recurse on ancestors.
        if feature.is_recursive():
            for parent_key in feature.parents:
                # Call parent to refresh recursively; increment stack depth
                parent_is_stale = feature.parents[parent_key]\
                                  .touch(initiating_call=this_call, is_stale=0)
                is_stale |= parent_is_stale
        # If stale for some other reason, also flag to be updated.
        feature_expired = feature._expired(call_record=this_call)
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
        # Finally, pass along return value of fn: this wrapper should be purely
        # impure
        return return_value
    wrapped_fn.is_refresh = True
    return wrapped_fn


def include_feature(feature_class, query_name):
    """
    Either return an existing document, if one exists, or create a new one and
    return it.

    Note that this kind of function is deemed unsafe by the mongoengine docs,
    since MongoDB lacks transactions. This might be an important design
    consideration, so keep an eye on this.

    Note that the equivalent deprecated moongoengine function is called
    `get_or_create`.

    Note, further, that it maybe considered poor practice to rely on an
    exception as an ordinary application logic signal.
    """
    try:
        doc = feature_class.objects.get(name=query_name)
    except DoesNotExist:
        doc = feature_class(name=query_name)
    except MultipleObjectsReturned:
        # Don't do anything yet; just propagate the exception
        raise MultipleObjectsReturned
    return doc


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
    # Time when last updated
    timestamp = DateTimeField(default=dt.datetime.now())
    is_stale_func = StringField(max_length=60)
    refresh_func = StringField(max_length=60)
    parents = DictField(default={})

    def __init__(self, **kwargs):
        # Create a new document
        super().__init__(**kwargs)
        self.save()

    def _status(self):
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
        if self._expired() | self.manual_expiration_switch:
            s = messages.cstr(self.name, 'fail')
        else:
            s = messages.cstr(self.name, 'ok')
        # Descriptor of this feature
        s += '\t: ' + messages.cstr(self.__class__.__name__, 'bold')
        # This feature's status
        status = self._status()
        if status:
            s += '\n' + status
        if self.parents:
            s += '\n\t'
            for p in self.parents.values():
                parent_str = p.__str__()
                s += '\n\t'.join(parent_str.split('\n'))

        return s

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

    def __call__(self, initiating_call=None, **kwargs):
        """
        Feature is callable. This method does whatever is needed to update an
        expired feature.
        By default, calling the instance only refreshes
        and logs. Unless overwritten, just updates the time-since-refresh and
        returns itself. This strikes me as a convenient expressionn of intent
        in some ways, but it's also a little unpythonic: "explicit is better
        than implicit".
        """
        self.timestamp = dt.datetime.now()
        return

    @refresh
    def touch(self, initiating_call=None, is_stale=False) -> bool:
        """
        Manually refresh the feature without doing anything else. This method
        has a special role, being invoked by DySART as the default refresh
        method called as it climbs the feature tree. It's also treated in a
        special way by @refresh, in order to propagate refresh data downstream.
        While this does work, it's a little bit unpythonic: "explicit is better
        than implicit".
        In short, this is a hack, and it shouldn't last.
        """
        return is_stale

    def _expired(self, call_record=None) -> bool:
        """
        Check for feature expiration. By default, everything is a twinkie.
        """

        return False

    def set_expired(self, is_expired: bool = True) -> None:
        """
        Provide an interface to manually set the expiration state of a feature.
        """
        self.manual_expiration_switch = is_expired
        self.save()

    def update(self):
        pass

    def is_recursive(self) -> bool:
        """
        Does dependency-checking recurse on this feature? By default, yes.
        Even though this does nothing now, I'm leaving it here to indicate that
        a feature might take its place in the future.
        """
        return True

    def add_parents(self, *new_parents) -> bool:
        """
        Insert a dependency into the feature's parents list and write to the
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
    uid_len = 40

    meta = {'allow_inheritance': True}
    initiating_call = ReferenceField('self', required=False)
    level = IntField(default=0)
    feature = ReferenceField('Feature')
    uid = StringField(default='', max_length=uid_len, required=True, primary_key=True)
    timestamp = DateTimeField(default=dt.datetime.now())
    user_id = StringField(max_length=255)
    exit_status = StringField(default='OK')

    def __init__(self, feature, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.initiating_call = initiating_call
        self.feature = feature
        self.timestamp = dt.datetime.now()
        if self.initiating_call is None:
            self.level = 0
        else:
            self.level = self.initiating_call.level + 1

        # Generate a uid
        # TODO really this should be a hash of the called feature's state
        h = hashlib.sha1(str.encode(self.feature.name))
        if self.initiating_call is None:
            h.update(str.encode(str(self.timestamp)))
        else:
            h.update(str.encode(self.initiating_call.uid))
        self.uid = h.hexdigest()[:CallRecord.uid_len]

        self.user_id = getpass.getuser()

        self.save()

    def get_initiated_call(self, other_feature):
        # Should search tree for a matching call.
        return
