#!/usr/bin/env python

if __name__ == "__main__":
    import dev_appserver
    dev_appserver.fix_sys_path()

import os, webapp2, logging, datetime
from xml.dom.minidom import Text, Element, Document

from models import SharkAttack, Country, Country, Area
from utils import StringUtils
from repositories import SharkAttackRepository, CountryRepository, AreaRepository

class SiteMapUrl():
    def __init__(self, path, lastmod, changefreq, priority):
        self.path = path
        self.lastmod = lastmod
        self.changefreq = changefreq
        self.priority = priority

class SiteMapGenerator:
    def __init__(self, urlScheme, hostName):
        self._hostName = hostName
        self._urlScheme = urlScheme
        self._baseUrl = "%s://%s" % (self._urlScheme, self._hostName)
        self._urls = []
        
    def addUrl(self, url):
        self._urls.append(url)

    def __appendElementWithTextNode(self, doc, parent, tagName, text):
        elem = doc.createElement(tagName)
        textNode = doc.createTextNode(text)
        elem.appendChild(textNode)
        parent.appendChild(elem)

    def __appendUrlXml(self, doc, root, url):
        urlElem = doc.createElement("url")
        self.__appendElementWithTextNode(doc, urlElem, "loc", self._baseUrl + url.path)
        if url.lastmod is not None:
            self.__appendElementWithTextNode(doc, urlElem, "lastmod", url.lastmod.isoformat())
        self.__appendElementWithTextNode(doc, urlElem, "changefreq", url.changefreq)
        self.__appendElementWithTextNode(doc, urlElem, "priority", str(url.priority))
        root.appendChild(urlElem)

    def generateXml(self):
        doc = Document()
        root = doc.createElement("urlset")
        root.setAttribute("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

        for url in self._urls:
            self.__appendUrlXml(doc, root, url)

        doc.appendChild(root)
        return doc.toprettyxml()


class SiteMap(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self._hostName = os.environ.get("HTTP_HOST")
        self._urlScheme = os.environ.get("wsgi.url_scheme")
        self._sharkAttackRepository = SharkAttackRepository()
        self._countryRepository = CountryRepository()
        self._areaRepository = AreaRepository()
        self._smg = SiteMapGenerator(self._urlScheme, self._hostName)

    def __getCountryUrl(self, countryId):
        return "/place/%s" % countryId

    def __getAreaUrl(self, countryId, areaId):
        return "/place/%s/%s" % (countryId, areaId)

    def __getAttackUrl(self, countryId, areaId, attackId):
        return "/attack/%s/%s/%s" % (countryId, areaId, attackId)

    def getXml(self):
        self._smg.addUrl(SiteMapUrl("/", None, "weekly", 1.0))
        self._smg.addUrl(SiteMapUrl("/places", None, "weekly", 1.0))
        for country in self._countryRepository.getCountries():
            self._smg.addUrl(SiteMapUrl(self.__getCountryUrl(country.urlPart), None, "weekly", 0.9))
            for area in self._areaRepository.getAreasOfCountryForId(country.urlPart):
                self._smg.addUrl(SiteMapUrl(self.__getAreaUrl(country.urlPart, area.urlPart), None, "weekly", 0.8))
                for attack in self._sharkAttackRepository.getDescendantAttacksForKey(area.key):
                    self._smg.addUrl(SiteMapUrl(self.__getAttackUrl(country.urlPart, area.urlPart, attack.gsaf_case_number), None, "monthly", 0.5))
        return self._smg.generateXml()

    def get(self):
        self.response.headers['Content-Type'] = "application/xml; charset=utf-8"
        self.response.out.write(self.getXml())



if __name__ == "__main__":
    import dev_appserver
    dev_appserver.fix_sys_path()
    from mocks.repositories import SharkAttackRepository, CountryRepository, AreaRepository

    smg = SiteMapGenerator("http", "www.blah.com")
    smg.addUrl(SiteMapUrl("/foo", datetime.date(2014, 1, 1), "monthly", 0.5))
    smg.addUrl(SiteMapUrl("/bar", None, "monthly", 0.5))
    print smg.generateXml()


    sm = SiteMap(None, None)
    print sm.getXml()

    
