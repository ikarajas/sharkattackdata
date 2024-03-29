import logging
from basepage import *
from models.native import Country, Area, SharkAttack
from repositories.general import SiteInformationRepository
from repositories.data.common import *
from repositories.data.repository_pickle import SharkAttackRepository


class MainPage(BasePage):
    def handle(self):
        return {
            "breadcrumb_data": self.getBreadcrumbData(None),
            "last_attacks": self._sharkAttackRepository.getLastTenAttacks()
            }

class LinksPage(BasePage):
    def handle(self):
        return {
            "subtemplate": self.resolveTemplatePath("links.html")
            }

class SiteMaintenancePage(BasePage):
    def __init__(self, request, response):
        super(SiteMaintenancePage, self).__init__(request, response)
        self._isSiteMaintenancePage = True

    def handle(self):
        si = self._siteInformationRepository.get()

        if si.status == SiteInformation.STATUS_ONLINE:
            raise PageNotFoundException(correctPath="/")

        statusMessage = si.message
        if statusMessage in (None, ""):
            statusMessage = "The site is currently under maintenance."
        return {
            "subtemplate": self.resolveTemplatePath("site-maintenance.html"),
            "statusMessage": statusMessage
            }

class SharkAttacksByLocationPage(BasePage):
    def __init__(self, request, response):
        super(SharkAttacksByLocationPage, self).__init__(request, response)

    def handle(self):
        return {
            "subtemplate": self.resolveTemplatePath("places.html"),
            "title": "Shark Attacks by Country",
            "meta_description": "A list of countries in which shark attacks are recorded. Click on a country to show more information.",
            "highest_total": sorted(self.helper.getCountries(), key=lambda c: c.count_unprovoked, reverse=True)[0].count_unprovoked,
            "countries": sorted(self.helper.getCountries(), key=lambda c: c.count_unprovoked, reverse=True)
            }

class AttackPage(BasePage):
    def __init__(self, request, response):
        super(AttackPage, self).__init__(request, response)

    def getUrlForAttack(self, attack, isGsaf):
        path = [""]
        if isGsaf:
            path.append("gsaf")
        path.extend(["attack", attack.countryNormalised, attack.area_normalised, attack.gsaf_case_number])
        logging.info(path)
        return "/".join(path)

    def handle(self, countryId, areaId, attackId):
        response = self._sharkAttackRepository.getFullyResolvedAttack(countryId, areaId, attackId)

        if response.status == FullyResolvedAttackStatus.NotFound:
            raise PageNotFoundException()
        elif response.status == FullyResolvedAttackStatus.FoundInDifferentLocation:
            raise PageNotFoundException(correctPath=self.getUrlForAttack(response.attack, False))
        else:
            area = self._areaRepository.getArea(response.countryId, response.areaId)
            country = self._countryRepository.getCountry(response.countryId)
            return {
            "subtemplate": self.resolveTemplatePath("attack.html"),
            "title": "Shark attack at %s in %s, %s" % (response.attack.location, area.name, country.name),
            "meta_description": "Details of a shark attack that occurred %s at %s in %s, %s." % \
                (response.attack.date_userfriendly, response.attack.location, area.name, country.name),
            "attack": response.attack,
            "breadcrumb_data": self.getBreadcrumbData(response.attack)
            }

class LocationPage(BasePage):
    def __init__(self, request, response):
        super(LocationPage, self).__init__(request, response)

    def handle(self):
        return {}

class CountryPage(LocationPage):
    def __init__(self, request, response):
        super(CountryPage, self).__init__(request, response)

    def onGet(self, countryNameKey):
        self._country = self._countryRepository.getCountry(self.helper.getNormalisedCountryName(countryNameKey))
        if self._country is None:
            return
        self._areas = self._country.areas

    def handle(self, countryNameKey):
        self.onGet(countryNameKey)
        if self._country is None:
            raise PageNotFoundException()

        return {
            "title": "Shark Attack Data: %s" % self._country.name,
            "subtemplate": self.resolveTemplatePath("country.html"),
            "country": self._country,
            "areas": sorted(self._areas, key=lambda a: a.name), #needed by GSAF page
            "breadcrumb_data": self.getBreadcrumbData(self._country),
            "meta_description": "A complete list of the shark attacks that have occurred in %s." % self._country.name
            }

class CountryOverviewPage(CountryPage):
    def __init__(self, request, response):
        super(CountryOverviewPage, self).__init__(request, response)

    def handle(self, countryNameKey):
        self.onGet(countryNameKey)
        if self._country is None:
            raise PageNotFoundException()

        return {
            "title": "Shark Attack Data: %s" % self._country.name,
            "subtemplate": self.resolveTemplatePath("countryOverview.html"),
            "country": self._country,
            "breadcrumb_data": self.getBreadcrumbData(self._country),
            "areas": sorted(self._areas, key=lambda a: a.name),
            "meta_description": "An overview of the shark attacks that have occurred in %s. " % (self._country.name) + \
                "Provides statistical information including a timeline of unprovoked attacks as well as a graph of overall trends." 
            }

class AreaPage(LocationPage):
    def __init__(self, request, response):
        super(AreaPage, self).__init__(request, response)

    def handle(self, countryNameKey, areaNameKey):
        country = self._countryRepository.getCountry(self.helper.getNormalisedCountryName(countryNameKey))
        if country is None:
            raise PageNotFoundException()

        area = country.areas_dict[areaNameKey]
        if area is None:
            raise PageNotFoundException()

        return {
            "subtemplate": self.resolveTemplatePath("area.html"),
            "title": "Shark Attack Data: %s, %s" % (area.name, country.name),
            "country": country,
            "area": area,
            "breadcrumb_data": self.getBreadcrumbData(area),
            "meta_description": "A complete list of the shark attacks that have occurred in %s, %s." % (area.name, country.name)
            }

