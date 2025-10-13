class Router:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
    def ping(self):
        debug("Router ok")
    def setLevel(self, v: float):
        self.ownerComp.par.Level = v
        debug("Level -> {}".format(v))
