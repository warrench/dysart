
class RemoteObject:

    def __init__(self, cls, name):
        self.cls = cls
        self.name = name

    def __getattr__(self, attr):
        try:
            return self.__dict__[attr]
        except:
            return attr


class RemoteAttribute:

    def __init__(self, obj, name):
        self.obj
        self.name = name

    def __call__(self):
        pass


class RemoteProject(RemoteObject):

    def __init__(self, name):
        pass
