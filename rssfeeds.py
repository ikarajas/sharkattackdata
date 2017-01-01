#!/usr/bin/env python

import os, webapp2, logging, datetime
from xml.dom.minidom import Text, Element, Document

from models import SharkAttack, Country, Country, Area
from utils import StringUtils
from repositories.data.repository_ndb import SharkAttackRepository, CountryRepository, AreaRepository, DataHelper

class FeedItem:
    title = None
    link = None
    description = None
    subPlaceFeedLink = None
    attackFeedLink = None
    def __init__(self, title, link, description, subPlaceFeedLink=None, attackFeedLink=None):
        self.title = title
        self.link = link
        self.description = description
        self.subPlaceFeedLink = subPlaceFeedLink
        self.attackFeedLink = attackFeedLink

class RssFeed(webapp2.RequestHandler):
    _feedTitle = None
    _feedLink = None
    _feedDescription = None
    def __init__(self, request, response):
        self.initialize(request, response)
        isGsaf = request.path.startswith("/gsaf")
        self._hostName = os.environ.get("HTTP_HOST")
        self._urlScheme = os.environ.get("wsgi.url_scheme")
        self._sharkAttackRepository = SharkAttackRepository()
        self._countryRepository = CountryRepository()
        self._areaRepository = AreaRepository()
        self._dataHelper = DataHelper()
        self._baseUrl = "%s://%s/%s" % (self._urlScheme, self._hostName, "gsaf/" if isGsaf else "")
        self._feedsBaseUrl = "%sfeeds/" % self._baseUrl

    def _configure(self, feedTitle, feedLink, feedDescription):
        self._feedTitle = feedTitle
        self._feedLink = feedLink
        self._feedDescription = feedDescription

    def _makeElementWithTextNode(self, tagName, text):
        elem = Element(tagName)
        textNode = Text()
        textNode.data = text
        elem.appendChild(textNode)
        return elem
        
    def _appendElementWithTextNode(self, appendTo, tagName, text):
        appendTo.appendChild(self._makeElementWithTextNode(tagName, text))

    def get(self, *args):
        self.response.headers['Content-Type'] = "application/rss+xml"

        items = self.getItems(*args)

        itemElems = []
        for item in items:
            itemElem = Element("item")
            self._appendElementWithTextNode(itemElem, "title", item.title)
            self._appendElementWithTextNode(itemElem, "link", item.link)
            self._appendElementWithTextNode(itemElem, "description", item.description)
            self._appendElementWithTextNode(itemElem, "guid", item.link)
            if item.subPlaceFeedLink:
                self._appendElementWithTextNode(itemElem, "sharkattackdata:subPlaceFeedLink", item.subPlaceFeedLink)
            if item.attackFeedLink:
                self._appendElementWithTextNode(itemElem, "sharkattackdata:attackFeedLink", item.attackFeedLink)

            itemElems.append(itemElem)

        # Need to make channel element after the generator returned by getItems has been iterated.
        channelElem = Element("channel")
        self._appendElementWithTextNode(channelElem, "title", self._feedTitle)
        self._appendElementWithTextNode(channelElem, "link", self._feedLink)
        self._appendElementWithTextNode(channelElem, "description", self._feedDescription)

        for itemElem in itemElems:
            channelElem.appendChild(itemElem)

        responseText = """<?xml version="1.0"?>
<rss version="2.0" xmlns:sharkattackdata="http://sharkattackdata.com/rss/modules/1.0/">
%s
</rss>
""" % (channelElem.toprettyxml())
        self.response.out.write(responseText)

class CountryFeed(RssFeed):
    def __init__(self, *args):
        super(CountryFeed, self).__init__(*args)

    def getItems(self):
        self._configure("Countries", "%splace" % (self._baseUrl), "Countries where incidents have occurred.")
        for country in self._countryRepository.getCountries():
            yield FeedItem(country.name, "%splace/%s" % (self._baseUrl, country.urlPart), "Country of %s." % country.name,
                           subPlaceFeedLink="%splaces/%s.xml" % (self._feedsBaseUrl, country.urlPart),
                           attackFeedLink="%sattacks/%s.xml" % (self._feedsBaseUrl, country.urlPart))
    
class AreaFeed(RssFeed):
    def __init__(self, *args):
        super(AreaFeed, self).__init__(*args)

    def getItems(self, countryKey):
        country = self._countryRepository.getCountry(countryKey)
        if country is None:
            self.abort(404)
        self._configure("Areas in %s" % country.name, "%splace/%s" % (self._baseUrl, country.urlPart),
                        "Areas in %s where incidents have occurred." % country.name)
        for area in self._areaRepository.getAreasOfCountry(country):
            yield FeedItem(area.name, "%splace/%s/%s" % (self._baseUrl, country.urlPart, area.urlPart),
                           "%s, %s." % (area.name , country.name),
                           attackFeedLink="%sattacks/%s/%s.xml" % (self._feedsBaseUrl, country.urlPart, area.urlPart))
    
class SharkAttackFeed(RssFeed):
    def __init__(self, *args):
        super(SharkAttackFeed, self).__init__(*args)

    def getItems(self, *args):
        countryKey = args[0]
        areaKey = None
        if len(args) > 1:
            areaKey = args[1]
        parentCountry = None
        title = None
        link = None
        if areaKey is None:
            node = self._countryRepository.getCountry(countryKey)
            if node is None:
                self.abort(404)
            title = "Shark Attacks in %s" % node.name
        else:
            node = self._areaRepository.getArea(countryKey, areaKey)
            if node is None:
                self.abort(404)
            parentCountry = self._dataHelper.getNodeParent(node)
            title = "Shark Attacks in %s, %s" % (node.name, parentCountry.name)

        link = self._baseUrl + "place"

        self._configure(title, link, title)
        for attack in self._sharkAttackRepository.getDescendantAttacksForKey(node.key):
            attackTitle = "%s at %s, %s" % (attack.date_userfriendly, attack.location, attack.area)
            yield FeedItem(
                attackTitle,
                "%sattack/%s/%s/%s" % (
                    self._baseUrl,
                    attack.countryNormalised,
                    attack.area_normalised,
                    self._dataHelper.getNodeId(attack)),
                attackTitle)
    
