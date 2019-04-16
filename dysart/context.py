class Context:
    """
    This class is sort of an ugly god object that I'm using to pass globals
    around without polluting the global namespace. I think this is considered
    pretty bad practice, but it works for now. Hopefully this won't necessitate
    a major refactoring later on.
    """
    db_client =     None
    labber_client = None
