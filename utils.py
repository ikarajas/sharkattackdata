import re
import unittest
import unicodedata

class MiscUtils:
    @staticmethod
    def uniqueify(seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if x not in seen and not seen_add(x)]


class StringUtils:
    @staticmethod
    def normalisePlaceName(name):
        return StringUtils.normaliseName(name, toLower=True, spacesToUnderscore=True, unicodeToAscii=True)

    @staticmethod
    def normaliseName(name, toLower=False, spacesToUnderscore=False, spacesToDash=False, dashesToUnderscore=False, unicodeToAscii=False):
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
        if unicodeToAscii:
            name = StringUtils.toAscii(name)

        alnumRe = re.compile(r"([^a-zA-Z0-9_\- ]+)")
        name = alnumRe.sub("", name)
        return name

    @staticmethod
    def toAscii(inStr):
        if not isinstance(inStr, unicode):
            return inStr
        return unicodedata.normalize("NFKD", inStr).encode("ascii", "ignore")

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

    def testUnicodeToAscii(self):
        initial = u"\u0107"
        self.assertTrue(isinstance(initial, unicode))
        decoded = StringUtils.normaliseName(u"\u0107", unicodeToAscii=True)
        self.assertFalse(isinstance(decoded, unicode))
        self.assertEqual(decoded, "c")

    def testUnicodeToAsciiIsOff(self):
        initial = u"\u0107"
        self.assertTrue(isinstance(initial, unicode))
        decoded = StringUtils.normaliseName(u"\u0107", unicodeToAscii=False)
        self.assertTrue(isinstance(decoded, unicode))
        # The alphanumeric regex will not match a unicode character, so it will be removed.
        self.assertEqual(decoded, "")

if __name__ == "__main__":
    unittest.main()


