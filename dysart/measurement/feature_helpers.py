class CallerMessage():
    """
    Messenger passed along with a feature call to dependencies, containing some
    """

    def __init__(self, issuer, message='', level=0):
        self.timestamp = dt.datetime.now()
        self.issuer = issuer
        self.message = message
        self.level = level

# Worry about these later, after the structure of @refresh is pretty much set.

def aged_out(self, level=0):
    """
    Check whether timestamp is too old.
    """
    t_now = dt.datetime.now()
    delta_t = t_now - self.timestamp
    return delta_t > self.age_out_time


def dependencies_stale(self, level=0):
    """
    Recursively check whether dependencies have gone stale
    """
    for dep in self.dependencies:
        if dep.is_stale(level=level):
            return True
    return False


def dependencies_or_age(self, level=0):
    """
    Either dependencies have gone stale or it has aged out
    """
    return self.aged_out(level=level) or self.dependencies_stale(level=level)

    #############################
    # `refresh` implementations #
    #############################


def refresh_dependencies(self, level=0):
    """
    Recursively refresh all dependencies and reset timestamp. Note how silly it
    is that this traverses the whole tree already visited by dependencies_stale
    """
    for dep in self.dependencies:
        if dep.is_stale(level=level):
            dep.refresh(level=level)
        self.timestamp = dt.datetime.now()
