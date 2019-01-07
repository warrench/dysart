

class Feature:
    """
    """

    def __init__(self, cal_func=(lambda: None)):
        self.cal = cal_func
        self.handle = handle_func
        self.calibrated = False

    def set_parents(*parents):
        self.parents = set(parents)
        # Add self to children of new parent
        for parent in self.parents:
            parent.children.add(self)

    def flag_uncalibrated(self):
        for child in self.children():
            child.flag_uncalibrated()
        self.__calibrated = False

    def flag_calibrated(self):
        self.__calibrated = True


class FeatureDag:

    def __init__(self, features=set([]), handle=(lambda: None), self.register=(lambda: None)):
        self.features = features
        # User-configurable error-handling function
        self.handle = handle
        # Log the changes after calibration
        self.register = register

    def is_acyclic(self):
        # TODO
        pass

    def is_connected(self):
        # TODO
        pass

    def recursive_call(feature, **kwargs):
        # Possibly log things that could change for the benefit of self.handle.
        # We don't want to lose all our

        # TODO: check for cyclicity
        if feature.is_calibrated:
            return
        try:
            # Recursively calibrate everything upstream, then self
            for parent in feature.parents():
                self.recursive_cal(feature, **kwargs)
            feature.cal(**kwargs)
        except Exception as inst:
            self.handle(inst)
            return
        feature.flag_calibrated()
        return
