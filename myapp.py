# -*- coding: UTF-8 -*-
import os
import logging

import webapp2
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from bsuirschedule import bsuirparser
from models import GroupSchedule
import datetime


MAX_CACHING_TIME = 24 * 60 * 60
MAX_DB_TIME = 5*24*60*60

def fetchrawtable(group):
    data = memcache.get(group)
    if data is not None: # данные находятся в кэше
        logging.info("Get data for %s from cache" % group)
        return data
    else:
        # Нет в кэше
        q = GroupSchedule.all()
        q.filter("group = ", str(group))
        results = q.fetch(1)
        logging.debug("Fetching from DB")
        if results:
            schedule = results[0]
            if (datetime.datetime.now() - schedule.date).total_seconds() < MAX_DB_TIME:
                # в БД
                memcache.set(group, schedule.text, MAX_CACHING_TIME)
                logging.info("Get data for %s from db and save to cache" % group)
                return schedule.text
            else:
                # в БД просрочено, попытка нового запроса
                data = bsuirparser.fetch(group)
                if not data:
                    memcache.set(group, schedule.text, MAX_CACHING_TIME)
                    logging.info("Data in DB is too old, but site isn't respond %s save to cache" % group)
                    return schedule.text
                else:
                    schedule.delete()
                    memcache.set(group, data, MAX_CACHING_TIME)
                    logging.info("Get new data for %s and save to cache" % group)
                    GroupSchedule(group=group, text=data).put()
                    return data



        else: # нет в БД
            data = bsuirparser.fetch(group)
            if not data:
                logging.info("Fetching %s failed" % group)
                return None
            memcache.set(group, data, MAX_CACHING_TIME)
            logging.info("Get new data for %s and save to cache" % group)
            GroupSchedule(group=group, text=data).put()
            return data


class MainPage(webapp2.RequestHandler):
    def get(self, additional_path):
        path = os.path.join(os.path.dirname(__file__),
                                'templates', 'index.html')
        self.response.out.write(template.render(path, {}))
        return

class GroupSchedulePage(webapp2.RequestHandler):
    def get(self):

        group = self.request.get("group")
        subgroup = self.request.get("subgroup", None)
        week = self.request.get("week", None)
        if not group: #main page
            self.redirect("/")
        else:
            rawtable = fetchrawtable(group)
            if not rawtable:
                path = os.path.join(os.path.dirname(__file__),
                                    'templates', 'erroratbsuir.html')
                self.response.out.write(template.render(path,
                                        {'group': group}))
                return
            parsed = bsuirparser.parse(rawtable, subgroup, week)
            if parsed:
                path = os.path.join(os.path.dirname(__file__),
                                    'templates', 'schedule.html')
                logging.debug(parsed)
                self.response.out.write(template.render(path, {"week": parsed,
                                        "group": group, "subgroup": subgroup,
                                        "selweek": week,
                                        "weeknumbers": range(1, 5)})
                                        )
            else:
                self.response.headers['Content-Type'] = 'text/plain'
                self.response.out.write(u"Что-то пошло не так")
                logging.debug(u"Ошибка при разборе расписания")


app = webapp2.WSGIApplication([
                                ('/(home)?', MainPage),
                                ('/weekschedule',GroupSchedulePage)

                                ])
