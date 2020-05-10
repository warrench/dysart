"""
Utilities for pre- and post-refresh hooks
"""

from typing import Callable

def pre_hook(fn: Callable) -> Callable:
    """
    Decorates a function as a pre-refresh hook. This does a few things:
    * adds a flag for introspection
    * may trigger logging actions (future)

    Args:
        fn: The function to be wrapped

    Returns:
        The decorated pre-hook function
    """
    # flag the argument as a pre-hook
    fn.pre_hook = True
    return fn

def post_hook(fn: Callable) -> Callable:
    """
    Decorates a function as a post-refresh hook. This does a few things:
    * adds a flag for introspection
    * may trigger logging actions (future)

    Args:
        fn: The function to be wrapped

    Returns:
        The decorated post-hook function
    """
    # flag the argument as a post hook
    fn.post_hook = True
    return fn

@pre_hook
def debug(record):
    print(f"DEBUG PRE-HOOK: executing feature {record.feature.id}")
