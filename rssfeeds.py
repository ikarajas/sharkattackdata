#!/usr/bin/env python

import os, webapp2, logging, datetime

from models import SharkAttack, Country, Country, Area
from utils import StringUtils
from repositories import SharkAttackRepository, CountryRepository, AreaRepository

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
        self._baseUrl = "%s://%s/%s" % (self._urlScheme, self._hostName, "gsaf/" if isGsaf else "")
        self._feedsBaseUrl = "%sfeeds/" % self._baseUrl
    def _configure(self, feedTitle, feedLink, feedDescription):
        self._feedTitle = feedTitle
        self._feedLink = feedLink
        self._feedDescription = feedDescription

    def get(self, *args):
        self.response.headers['Content-Type'] = "application/rss+xml"
        rssItems = []
        for item in self.getItems(*args):
            subPlaceFeedText = "\n        <sharkattackdata:subPlaceFeedLink>%s</sharkattackdata:subPlaceFeedLink>" % item.subPlaceFeedLink \
                          if item.subPlaceFeedLink else ""
            attackFeedText = "\n        <sharkattackdata:attackFeedLink>%s</sharkattackdata:attackFeedLink>" % item.attackFeedLink \
                          if item.attackFeedLink else ""

            text = """
    <item>
        <title>%s</title>
        <link>%s</link>
        <description>%s</description>%s%s
    </item>
    """ % (item.title, item.link, item.description, subPlaceFeedText, attackFeedText)
            rssItems.append(text)
        responseText = """<?xml version="1.0"?>
<rss version="2.0" xmlns:sharkattackdata="http://sharkattackdata.com/rss/modules/1.0/">
    <channel>
        <title>%s</title>
        <link>%s</link>
        <description>%s</description>
    </channel>
    %s
</rss>
""" % (self._feedTitle, self._feedLink, self._feedDescription, "".join(rssItems))
        self.response.out.write(responseText)

class CountryFeed(RssFeed):
    def __init__(self, *args):
        super(CountryFeed, self).__init__(*args)

    def getItems(self):
        self._configure("Countries", "%splace" % (self._baseUrl), "Countries where incidents have occurred.")
        for country in self._countryRepository.getCountries():
            yield FeedItem(country.name, "%splace/%s" % (self._baseUrl, country.urlPart), "Country of %s." % country.name,
                           subPlaceFeedLink="%splaces/%s.rss" % (self._feedsBaseUrl, country.urlPart),
                           attackFeedLink="%sattacks/%s.rss" % (self._feedsBaseUrl, country.urlPart))
    
class AreaFeed(RssFeed):
    def __init__(self, *args):
        super(AreaFeed, self).__init__(*args)

    def getItems(self, countryKey):
        country = self._countryRepository.getCountry(countryKey)
        self._configure("Areas in %s" % country.name, "%splace/%s" % (self._baseUrl, country.urlPart),
                        "Areas in %s where incidents have occurred." % country.name)
        for area in self._areaRepository.getAreasOfCountry(country):
            yield FeedItem(area.name, "%splace/%s/%s" % (self._baseUrl, country.urlPart, area.urlPart),
                           "%s, %s." % (area.name , country.name),
                           attackFeedLink="%sattacks/%s/%s.rss" % (self._feedsBaseUrl, country.urlPart, area.urlPart))
    
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
            title = "Shark Attacks in %s" % node.name
            link = self._baseUrl + "place"
        else:
            node = self._areaRepository.getArea(countryKey, areaKey)
            parentCountry = node.key.parent().get()
            title = "Shark Attacks in %s, %s" % (node.name, parentCountry.name)
            link = self._baseUrl + "place"

        self._configure(title, link, title)
        for attack in self._sharkAttackRepository.getDescendantAttacksForKey(node.key):
            attackTitle = "%s at %s, %s" % (attack.date_userfriendly, attack.location, attack.area)
            yield FeedItem(attackTitle, "%sattack/%s" % (self._baseUrl, attack.key.id()),
                           attackTitle)
    
