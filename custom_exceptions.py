class PageNotFoundException(Exception):
    def __init__(self, correctPath=None):
        self.correctPath = correctPath


if __name__ == "__main__":
    print "Testing"
    raise PageNotFoundException(correctPath="blah")
