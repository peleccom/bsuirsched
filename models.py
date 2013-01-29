# -*- coding: UTF-8 -*-
from google.appengine.ext import db


class GroupSchedule(db.Model):
    group = db.StringProperty(required=True)
    text = db.TextProperty()
    date = db.DateTimeProperty(auto_now=True)
