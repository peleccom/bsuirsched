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
import time


from pytz.gae import pytz


MAX_CACHING_TIME = 24 * 60 * 60
MAX_DB_TIME = 5*24*60*60

minsk_tz = pytz.timezone("Europe/Minsk")

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

class DaySchedulePage(webapp2.RequestHandler):

    def getajaxcontext(self, date=None, group=None, subgroup=None):
        group = self.request.POST.get("group", group)
        subgroup = bsuirparser.subgroup2int(self.request.POST.get("subgroup",subgroup))
        date_str=self.request.POST.get("date",date)
        logging.info(date_str)
        try:
            if date_str == "today":
                date = (datetime.datetime.now(tz = pytz.utc)).astimezone(minsk_tz)
            elif date_str == "tomorrow":
                date = (datetime.datetime.now(tz = pytz.utc) + datetime.timedelta(days=1)).astimezone(minsk_tz)
            else:

                date = minsk_tz.localize(datetime.datetime.strptime(date_str, "%d-%m-%Y"))
        except Exception:
            # Wrong date
            return
        if not group:
            return
        else:
            rawtable = fetchrawtable(group)
            if not rawtable:
                return
                #error bsuir
        weeknum = bsuirparser.getweeknum(date.year, date.month, date.day)
        if not weeknum:
            return
            #incorrectdate
        parsed = bsuirparser.parse(rawtable,subgroup,weeknum)
        if parsed:
            studyday = parsed.getDay(date.weekday())
            return {
                "default_group": hasdefaultgroup(self.request),
                "studyday":studyday,
                "target_date": date,
                "weeknum": weeknum,
                "group": group,
                "subgroup": subgroup
                }


    def get(self,date, group, subgroup):
        default_group = hasdefaultgroup(self.request) or {}
        if not group:
            group = default_group.get("group",None)
        if not subgroup:
            subgroup = default_group.get("subgroup",None)
        context = self.getajaxcontext(date, group, subgroup) or {}
        now = datetime.datetime.now(tz = pytz.utc).astimezone(minsk_tz)
        context.update({
                "default_group": hasdefaultgroup(self.request),
                "now_time":now
                })

        # Если не получены в параметрах подставляем стандартные
        context["group"] = context.get("group", default_group.get("group", None))
        context["subgroup"] = context.get("subgroup", default_group.get("subgroup", None))
        path = os.path.join(os.path.dirname(__file__),
                                'templates', 'dayschedule.html')
        self.response.out.write(template.render(path,
                    context
                ))
    def post(self, *args):
        context = self.getajaxcontext()
        if context:
            path = os.path.join(os.path.dirname(__file__),
                               'templates', 'dayscheduleajax.html')
            self.response.out.write(template.render(path,
                context
                ))
        else:
            return


class GroupSchedulePage(webapp2.RequestHandler):
    def get(self):

        group = self.request.get("group")
        subgroup = self.request.get("subgroup", None)
        week = self.request.get("week", None)
        subgroup = bsuirparser.subgroup2int(subgroup)
        week = bsuirparser.week2int(week)
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
                                (r'/(home)?', MainPage),
                                (r'/weekschedule',GroupSchedulePage),
                                (r'/dayschedule(?:/([^/]*))?(?:/([^/]*))?(?:/([^/]*))?',DaySchedulePage) # O_o

                                ])
