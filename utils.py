import re, unittest

class Utils:
    @staticmethod
    def normaliseName(name):
        re = re.compile(r"([^a-z]+)")

class UtilsTest(unittest.TestCase):
    def testBasic(self):
        pass

if __name__ == "__main__":
    unittest.main()


