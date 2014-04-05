import os, math, logging, datetime

from google.appengine.api import memcache
from google.appengine.ext import ndb

from models import SharkAttack, Country, Country, Area
from utils import StringUtils


class AttackParentNodeSummary:
    def __init__(self, attacks):
        self._totalCount = len(attacks)

class SharkAttackRepository:
    def __init__(self):
        self._attacksPerPart = 1000

    def getAttackNodeId(self, key):
        return "|".join(key.flat())

    def getAttackParentNodeSummaryKey(self, key):
        return "attacks_%s_summary" % self.getAttackNodeId(key)

    def getAttacksPartKey(self, key, part):
        return "attacks_%s_part_%s" % (self.getAttackNodeId(key), part)

    def readAttacksFromCache(self, key):
        summary = memcache.get(self.getAttackParentNodeSummaryKey(key))
        if summary is None:
            return None
        attacks = []
        numParts = int(math.ceil(float(summary._totalCount)/float(self._attacksPerPart)))
        for i in range(numParts):
            cacheKey = self.getAttacksPartKey(key, i)
            logging.info("Retrieving from cache: %s" % cacheKey)
            theseAttacks = memcache.get(cacheKey)
            if theseAttacks is None:
                return None
            attacks.extend(theseAttacks)
        return attacks
        
    def writeAttacksToCache(self, key, attacks):
        summary = AttackParentNodeSummary(attacks)
        if not memcache.add(self.getAttackParentNodeSummaryKey(key), summary):
            raise Exception("Unable to write attack parent node summary to memcache.")
        numParts = int(math.ceil(float(summary._totalCount)/float(self._attacksPerPart)))
        for i in range(numParts):
            cacheKey = self.getAttacksPartKey(key, i)
            logging.info("Writing to cache: %s" % cacheKey)
            if not memcache.add(cacheKey, attacks[(i*self._attacksPerPart):((i+1)*self._attacksPerPart)]):
                raise Exception("Unable to write attack parent node summary to memcache.")

    def getDescendantAttacksForKey(self, key):
        attacks = self.readAttacksFromCache(key)

        if attacks is None:
            logging.info("Cache miss: %s" % self.getAttackNodeId(key))
            attacks = [y for y in SharkAttack.query(ancestor=key).order(SharkAttack.date).iter()]
            self.writeAttacksToCache(key, attacks)

        return attacks
