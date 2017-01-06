import os

from repositories.data.repository_pickle import CountryRepository, DataHelper
from utils import StringUtils

class Helper():
    def __init__(self):
        self._countryRepository = CountryRepository()
        self._dataHelper = DataHelper()

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
        if self._dataHelper.nodeIsArea(node):
            countryNode = self._dataHelper.getNodeParent(node)
            return os.path.join(path, "place", self._dataHelper.getNodeId(countryNode), self._dataHelper.getNodeId(node))
        if self._dataHelper.nodeIsCountry(node):
            return os.path.join(path, "place" if isGsaf else "country-overview", self._dataHelper.getNodeId(node))

    def resolveTemplatePath(self, relativePath, isGsaf):
        parts = ["templates"]
        if isGsaf:
            parts.append("gsaf")
        else:
            parts.append("sharkattackdata")
        parts.append(relativePath)
        return "/".join(parts)


