import re, unittest

class StringUtils:
    @staticmethod
    def normaliseName(name, toLower=False, spacesToUnderscore=False, spacesToDash=False, dashesToUnderscore=False):
        if spacesToUnderscore and spacesToDash:
            raise ValueError("Kwargs: spacesToUnderscore and spacesToDash cannot both be true.")
        name = name.strip()
        if toLower:
            name = name.lower()
        whitespaceRe = re.compile(r"\s+")
        name = whitespaceRe.sub(" ", name)
        if dashesToUnderscore:
            name = name.replace("-", "_")
        if spacesToUnderscore:
            name = name.replace(" ", "_")
        if spacesToDash:
            name = name.replace(" ", "-")
        alnumRe = re.compile(r"([^a-zA-Z0-9_\- ]+)")
        name = alnumRe.sub("", name)
        return name

class StringUtilsTest(unittest.TestCase):
    def testToLowerIsOn(self):
        self.assertEqual(StringUtils.normaliseName("HELLO", toLower=True), "hello")
        
    def testToLowerIsOff(self):
        self.assertEqual(StringUtils.normaliseName("HELLO", toLower=False), "HELLO")

    def testSpacesToUnderscoreIsOn(self):
        self.assertEqual(StringUtils.normaliseName("the    quick brown     fox", spacesToUnderscore=True), "the_quick_brown_fox")
        
    def testSpacesToUnderscoreIsOff(self):
        self.assertEqual(StringUtils.normaliseName("the  quick brown  fox", spacesToUnderscore=False), "the quick brown fox")

    def testStripString(self):
        self.assertEqual(StringUtils.normaliseName("   hello   "), "hello")

    def testRemoveMultipleWhitespace(self):
        self.assertEqual(StringUtils.normaliseName("a    b  c      d e        f"), "a b c d e f")

    def testTabsToSingleSpace(self):
        self.assertEqual(StringUtils.normaliseName("a\t\tb\tc\t\t\t\t\td\te\t\tf"), "a b c d e f")

    def testRemoveNonAlphanumeric(self):
        self.assertEqual(StringUtils.normaliseName("!@#$%^&*()+hello_there[]\{}|;':\",./<>?"), "hello_there")

    def testDashesToUnderscoreTrue(self):
        self.assertEqual(StringUtils.normaliseName("i-am-a-monkey", dashesToUnderscore=True), "i_am_a_monkey")

    def testDashesToUnderscoreFalse(self):
        self.assertEqual(StringUtils.normaliseName("i-am-a-monkey"), "i-am-a-monkey")

    def testSpacesToDashTrue(self):
        self.assertEqual(StringUtils.normaliseName("i am a monkey", spacesToDash=True), "i-am-a-monkey")

    def testSpacesToDashFalse(self):
        self.assertEqual(StringUtils.normaliseName("i am a monkey"), "i am a monkey")

if __name__ == "__main__":
    unittest.main()


