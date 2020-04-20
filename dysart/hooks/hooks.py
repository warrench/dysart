"""
Utilities for pre- and post-refresh hooks
"""

from typing import Callable

def pre_hook(fn: Callable) -> Callable:
    """
    Decorates a function as a pre-refresh hook. This does a few things:
    * adds a flag for introspection
    * marks the function static, since it will be used as a class method
    * in the future, may trigger logging actions

    Args:
        fn: The function to be wrapped

    Returns:
        The decorated pre-hook function
    """
    # we expect this function to be used as a class attribute,
    # so make it static.
    fn = staticmethod(fn)
    # flag the argument as a pre-hook
    fn.pre_hook = True
    return fn

def post_hook(fn: Callable) -> Callable:
    """
    Decorates a function as a post-refresh hook. This does a few things:
    * adds a flag for introspection
    * marks the function static, since it will be used as a class method
    * in the future, may trigger logging actions

    Args:
        fn: The function to be wrapped

    Returns:
        The decorated post-hook function
    """
    # we expect this function to be used as a class attribute,
    # so make it static.
    fn = staticmethod(fn)
    # flag the argument as a post hook
    fn.post_hook = True
    return fn
