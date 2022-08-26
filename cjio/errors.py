import warnings


class CJInvalidOperation(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "InvalidOperation: %s" % self.msg


class CJInvalidVersion(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "InvalidVersion: %s" % self.msg


class CJWarning(Warning):
    def __init__(self, msg):
        super().__init__()
        self.msg = msg

    def __str__(self):
        return self.msg

    def warn(self):
        warnings.warn(self)
