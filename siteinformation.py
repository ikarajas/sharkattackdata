class SiteInformation:
    STATUS_OFFLINE = "offline"
    STATUS_ONLINE = "online"
    def __init__(self, status, message):
        if not (status in (SiteInformation.STATUS_ONLINE, SiteInformation.STATUS_OFFLINE)):
            raise ValueError("%s is not a valid status." % status)
        if message is None:
            raise ValueError("Message needs to have a value.")
        self.status = status
        self.message = message
