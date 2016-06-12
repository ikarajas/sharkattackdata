import os

from repositories import CountryRepository
from utils import StringUtils

class Helper():
    def __init__(self):
        self._countryRepository = CountryRepository()

    def uniqueify(self, seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if x not in seen and not seen_add(x)]

    def getCountries(self):
        return self._countryRepository.getCountries()

    def getNormalisedCountryName(self, countryName):
        return StringUtils.normalisePlaceName(countryName)

    def getCountriesAsDict(self):
        displayCountries = self.getCountries()
        return dict([[self.getNormalisedCountryName(y.name), y] for y in displayCountries])

    def getUrlForNode(self, site, node):
        path = "/"
        isGsaf = site == "gsaf"
        if isGsaf:
            path = os.path.join(path, "gsaf")
        if node is None:
            return path if isGsaf else os.path.join(path, "place")
        if node._get_kind() == "Area":
            return os.path.join(path, "place", node.key.parent().get().key.id(), node.key.id())
        if node._get_kind() == "Country":
            return os.path.join(path, "place" if isGsaf else "country-overview", node.key.id())

    def resolveTemplatePath(self, relativePath, isGsaf):
        parts = ["templates"]
        if isGsaf:
            parts.append("gsaf")
        else:
            parts.append("sharkattackdata")
        parts.append(relativePath)
        return "/".join(parts)

