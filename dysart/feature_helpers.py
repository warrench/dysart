class CallMessage():
    """
    Messenger passed along with a feature call to dependencies, containing some
    """

    def __init__(self, issuer, message='', level=0):
        self.timestamp = dt.datetime.now()
        self.issuer = issuer
        self.message = message
        self.level = level

def refresh(fn):
    """
    Decorator that flags a method as having dependencies and possible requiring
    a refresh operation. Recursively refreshes ancestors, then checks an
    additional condition `expired()` specified by the Feature class. If the
    feature or its ancestors have expired, perform the corrective operation
    defined by the _______ method.

    An advantage of using a refresh decorator to solve the dependency problem
    is that a given feature may have a variety of public methods with the same
    dependencies. This situation can be illustrated by a QubitRabi feature with
    public methods `pi_time` and `pi_2_time` accessed as properties:

        @refresh
        @property
        def pi_time(self):
            return self.data['pi_time']

        @refresh
        @property
        def pi_2_time(self):
            return self.data['pi_2_time']

    If we access qubit_rabi.pi_time followed by qubit_rabi.pi_2_time, they
    should use the same measurement & fit results to yield the

    This is a pretty central feature, and it must be done right. This should be
    a focus of any future code review, so
    """
    @wraps(fn)
    def wrapped(*args, **kwargs):
        # Sanitize the input in case a level wasn't passed.
        if 'level' in **kwargs:
            lvl = level
        else
            lvl = 0
        is_stale = False
        # if this call recurses, recurse on ancestors.
        if self.is_recursive() == True:
            for parent in self.parents:
                # TODO: implement this default refresh function
                # If an upstream feature expired, this feature needs to be
                # refreshed as well.
                is_stale |= refresh_parent(parent, level=lvl+1)
        # if stale for some other reason, refresh self.
        is_stale |= self.expired()
        # Do the requested operation!
        @logged(level)
        fn(*args, **kwargs)
        # Save any changes to the database
        self.save()
        # Finally, propagate expiration state downstream.
        return is_stale
    return wrapped



# Worry about these later, after the structure of @refresh is pretty much set.


def refresh(self, level=0):
	"""
	ibid
	"""
	return eval(self.refresh_func + '(self, level=level)')

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
	is that this traverses the whole tree already visited by dependencies_stale!
	"""
	for dep in self.dependencies:
		if dep.is_stale(level=level):
			dep.refresh(level=level)
	self.timestamp = dt.datetime.now()
