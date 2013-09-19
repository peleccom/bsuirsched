# -*- coding: UTF-8 -*-
from google.appengine.ext import ndb


class GroupSchedule(ndb.Model):
    group = ndb.StringProperty(required=True)
    schedule = ndb.PickleProperty()
    date = ndb.DateTimeProperty(auto_now=True)

class GroupsList(ndb.Model):
    groups_list = ndb.PickleProperty(required=True)
