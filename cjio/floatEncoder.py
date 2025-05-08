class FloatEncoder(float):
    __repr__ = staticmethod(lambda x: format(x, ".6f"))
