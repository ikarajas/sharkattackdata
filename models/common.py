class GsafIncidentType():
    PROVOKED = "Provoked"
    UNPROVOKED = "Unprovoked"
    BOATING = "Boating"
    SEA_DISASTER = "Sea Disaster"
    INVALID = "Invalid"

class PlaceSummary:
    totalCountAll = None
    unprovokedCount = None
    fatalAndUnprovokedCount = None
    nonFatalAndUnprovokedCount = None

    def __init__(self, attacks):
        attacks = [y for y in attacks]
        self.totalCountAll = len(attacks)
        self.unprovokedCount = len([y for y in attacks if y.unprovoked])
        self.fatalAndUnprovokedCount = len([y for y in attacks if y.fatal and y.unprovoked])
        self.nonFatalAndUnprovokedCount = len([y for y in attacks if y.unprovoked and (not y.fatal)])

    def __repr__(self):
        figures = (self.totalCountAll, self.unprovokedCount, self.fatalAndUnprovokedCount, self.nonFatalAndUnprovokedCount)
        return "Total: %s,  Unprovoked: %s, Fatal and Unprovoked: %s, Non-fatal and Unprovoked: %s" % figures

