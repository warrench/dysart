from functools import wraps

def registered(fn: Callable) -> Callable:
    """Marks a decorator to be registered when it is applied to a class method
    of a
    """

class RegisterClass(type):
    """A metaclass for classes that register decorated methods. This is used so
    that these classes can identify their methods, which otherwise would have
    to rely on function attributes. But these would not work, because
    `Document`s have an attribute `_collection`, whose `__getattr__` returns
    something for any argument.

    Note that custom metaclasses are _almost always_ considered an antipattern,
    since they tend to obfuscate class implementation and produce hidden
    side-effects. The one major exception to this rule is in writing
    frameworks, where this is exactly the desired outcome.
    """

    def __prepare__(name, bases, **kwds):

    def __new__(metacls, name, bases, namespace, *kwds):
