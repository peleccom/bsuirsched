# -*- coding: UTF-8 -*-
import os
import logging

import webapp2
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from bsuirschedule import bsuirparser


def fetchrawtable(group):
    data = memcache.get(group)
    if data is not None:
        logging.info("Get data for %s from cache" % group)
        return data
    else:
        data = bsuirparser.fetch(group)
        if not data:
            return None
        memcache.set(group, data, 24 * 60 * 60)
        logging.info("Get new data for %s and save to cache" % group)
        return data


class MainPage(webapp2.RequestHandler):
    def get(self):
        group = self.request.get("group")
        subgroup = self.request.get("subgroup", None)
        week = self.request.get("week", None)
        if not group:
            path = os.path.join(os.path.dirname(__file__),
                                'templates', 'index.html')
            self.response.out.write(template.render(path, {}))
            return
        else:
            rawtable = fetchrawtable(group)
            if not rawtable:
                self.response.headers['Content-Type'] = 'text/plain'
                self.response.out.write(u"Не удалось получить расписание")
                return
            parsed = bsuirparser.parse(rawtable, subgroup, week)
            if parsed:
                path = os.path.join(os.path.dirname(__file__),
                                    'templates', 'schedule.html')
                self.response.out.write(template.render(path, {"week": parsed,
                                        "group": group, "subgroup": subgroup,
                                        "selweek": week,
                                        "weeknumbers": range(1, 5)})
                                        )
            else:
                self.response.headers['Content-Type'] = 'text/plain'
                self.response.out.write(u"Что-то пошло не так")
                logging.debug(u"Ошибка при разборе расписания")

app = webapp2.WSGIApplication([('/', MainPage)])
