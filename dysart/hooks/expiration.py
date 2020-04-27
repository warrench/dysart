import datetime
from typing import Callable

from dysart.feature import Feature, ExpirationStatus


def always_fresh(feature: Feature) -> ExpirationStatus:
    """An expiration hook that considers its feature fresh no matter what,
    unless there is no measurement in the database!
    """
    return ExpirationStatus.FRESH


def always_expired(feature: Feature) -> ExpirationStatus:
    """An expiration hook that considers its feature expired no matter what.

    Todo:
        Avoid this one for now, because it *might* be afflicted by a bug
        that causes measurements to trigger more than once. Do test it,
        though!
    """
    return ExpirationStatus.EXPIRED


def timeout(**kwargs) -> Callable:
    """An expiration hook that considers its feature expired if the latest
    entry is older than a fixed delta. At the moment this works by checking
    when the last call was. You might want to change that by e.g. looking
    through the log_history.

    Args:
        **kwargs: Time delta should be passed in parameters "days", "hours",
        "minutes", "seconds", etc. with floating-point-convertible values.

    Returns: The expiration status, which is fresh if the feature has been
    updated more recently than the delta

    Todo:
        This also seems to fire _twice_. I really don't know why.
        Ok, it's firing once on each call to a @result method.
    """
    timeout_delta = datetime.timedelta(**kwargs)

    def hook(feature: Feature) -> ExpirationStatus:
        last_query = feature.call_records().order_by('-stop_time')[0]
        delta = datetime.datetime.now() - last_query.stop_time
        if delta > timeout_delta:
            return ExpirationStatus.EXPIRED
        else:
            return ExpirationStatus.FRESH

    return hook

