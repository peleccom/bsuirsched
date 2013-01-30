# -*- coding: UTF-8 -*-
import os
import logging

import webapp2
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from bsuirschedule import bsuirparser
from models import GroupSchedule
import datetime
import urllib


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
        q.filter("group = ", group)
        results = q.fetch(1)
        if results:
            schedule = results[0]
            if (datetime.datetime.now() - schedule.date).total_seconds() < MAX_DB_TIME:
                # в БД
                memcache.set(group, schedule.text, MAX_CACHING_TIME)
                logging.debug("Get data for %s from db and save to cache" % group)
                return schedule.text
            else:
                # в БД просрочено, попытка нового запроса
                data = bsuirparser.fetch(group)
                if not data:
                    memcache.set(group, schedule.text, MAX_CACHING_TIME)
                    logging.debug("Data in DB is too old, but site isn't respond %s save to cache" % group)
                    return schedule.text
                else:
                    schedule.delete()
                    memcache.set(group, data, MAX_CACHING_TIME)
                    logging.debug("Get new data for %s and save to cache" % group)
                    GroupSchedule(group=group, text=data).put()
                    return data



        else: # нет в БД
            data = bsuirparser.fetch(group)
            if not data:
                logging.error("Fetching %s failed" % group)
                return None
            memcache.set(group, data, MAX_CACHING_TIME)
            logging.debug("Get new data for %s and save to cache" % group)
            GroupSchedule(group=group, text=data).put()
            return data


def hasdefaultgroup(request):
    '''Return stored default group info'''
    if not request.cookies.has_key("default_group"):
        return None
    groupdic = {}
    groupdic["group"] = request.cookies.get("default_group")
    subgroup = request.cookies.get("default_subgroup", None)
    if subgroup:
        groupdic["subgroup"] = subgroup
    return groupdic

class MainPage(webapp2.RequestHandler):
    def get(self, additional_path):
        #Проверить куку и если установлена оправить напрямую
        if not additional_path:
            default_group_dic = hasdefaultgroup(self.request)
            if default_group_dic:
                try:
                    query_str = urllib.urlencode(default_group_dic)
                    self.redirect("/weekschedule?"+query_str)
                except Exception, e:
                    logging.error("Redirecting error : %s" % e)
                    self.redirect("/home")

        path = os.path.join(os.path.dirname(__file__),
                                'templates', 'index.html')
        self.response.out.write(template.render(path,
                {
                "default_group": hasdefaultgroup(self.request)
                }
                ))
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
                                        {'group': group,
                                        "default_group": hasdefaultgroup(self.request)
                                        }))
                return
            parsed = bsuirparser.parse(rawtable, subgroup, week)
            if parsed:
                path = os.path.join(os.path.dirname(__file__),
                                    'templates', 'schedule.html')
                self.response.out.write(template.render(path, {"week": parsed,
                                        "group": group, "subgroup": subgroup,
                                        "selweek": week,
                                        "weeknumbers": range(1, 5),
                                        "default_group": hasdefaultgroup(self.request)
                                        })
                                        )
            else:
                self.response.headers['Content-Type'] = 'text/plain'
                self.response.out.write(u"Что-то пошло не так")
                logging.debug(u"Ошибка при разборе расписания")


app = webapp2.WSGIApplication([
                                ('/(home)?', MainPage),
                                ('/weekschedule',GroupSchedulePage)

                                ])
