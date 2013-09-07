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


from pytz.gae import pytz

# os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'
# from django.conf import settings
# # Force Django to reload settings
# settings._target = None
# from django.utils import translation



MAX_CACHING_TIME = 24 * 60 * 60
MAX_DB_TIME = 5*24*60*60
DICTDATA_SCHEDULE_KEY_NAME = 'schedule'
DICTDATA_DATE_KEY_NAME = 'date'

minsk_tz = pytz.timezone("Europe/Minsk")

def get_group_data(group):
    """Return dictionary with schedule and date keys or None"""
    groupdata = memcache.get('group%s' % (group))

    if groupdata is not None: # данные находятся в кэше
        logging.info("Get data for %s from cache" % group)
        return groupdata
    else:
        # Нет в кэше
        group_schedule = GroupSchedule.query(GroupSchedule.group == group).get() # TODO: .get_by_id(...)
        if group_schedule:
            if (datetime.datetime.now() - group_schedule.date).total_seconds() < MAX_DB_TIME:
                # в БД
                dicdata = {
                    DICTDATA_SCHEDULE_KEY_NAME : group_schedule.schedule,
                    DICTDATA_DATE_KEY_NAME : group_schedule.date
                }
                memcache.set('group%s' % group, dicdata, MAX_CACHING_TIME)
                logging.info("Get data for %s from db and save to cache" % group)
                return dicdata
            else:
                logging.info("Old data in DB for %s" % group)
                # в БД просрочено, попытка нового запроса
                schedhtml = bsuirparser.fetch(group)
                if not schedhtml:
                    dicdata = {
                        DICTDATA_SCHEDULE_KEY_NAME: group_schedule.schedule,
                        DICTDATA_DATE_KEY_NAME: group_schedule.date
                    }
                    memcache.set('group%s' % group, dicdata , MAX_CACHING_TIME)
                    logging.info("Data in DB is too old, but site isn't respond. Old data %s save to cache" % group)
                    return dicdata
                else:
                    group_schedule.key.delete()
                    studyweek = bsuirparser.parse(schedhtml)
                    dbrec = GroupSchedule(group=group, schedule=studyweek)
                    dbrec.put()
                    dicdata = {
                        DICTDATA_SCHEDULE_KEY_NAME: studyweek,
                        DICTDATA_DATE_KEY_NAME: dbrec.date
                    }
                    memcache.set(group, dicdata, MAX_CACHING_TIME)
                    logging.info("Get new data for %s and save to cache" % group)
                    return dicdata



        else: # нет в БД
            schedhtml = bsuirparser.fetch(group)
            if not schedhtml:
                logging.error("Fetching %s failed" % group)
                return None
            else:
                studyweek = bsuirparser.parse(schedhtml)
                if not studyweek:
                    logging.error("Parsing %s failed" % group)
                    return None
                dbrec = GroupSchedule(group=group, schedule=studyweek)
                dbrec.put()
                dicdata = {
                    DICTDATA_SCHEDULE_KEY_NAME : studyweek,
                    DICTDATA_DATE_KEY_NAME : dbrec.date
                }
                memcache.set(group, dicdata, MAX_CACHING_TIME)
                logging.info("Get new data for %s and save to cache" % group)
                return dicdata


def get_preferred_group_params(request):
    """Return stored default group info"""
    if not request.cookies.has_key("default_group"):
        return None
    group_dic = {}
    group_dic["group"] = request.cookies.get("default_group")
    subgroup = request.cookies.get("default_subgroup", None)
    if subgroup:
        group_dic["subgroup"] = subgroup
    return group_dic

class MainPage(webapp2.RequestHandler):
    def get(self, additional_path):
        #Проверить куку и если установлена оправить напрямую
        if not additional_path:
            default_group_dic = get_preferred_group_params(self.request)
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
                "default_group": get_preferred_group_params(self.request)
                }
                ))
        return

class DaySchedulePage(webapp2.RequestHandler):

    def get_ajax_context(self, date=None, group=None, subgroup=None):
        group = self.request.POST.get("group", group)
        subgroup = bsuirparser.subgroup2int(self.request.POST.get("subgroup",subgroup))
        date_str=self.request.POST.get("date",date)
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
            group_data = get_group_data(group)
            if not group_data:
                return
                #error bsuir parser
        studyweek = group_data[DICTDATA_SCHEDULE_KEY_NAME]
        weeknum = bsuirparser.get_week_num(date.year, date.month, date.day)
        studyweek = studyweek.filter(subgroup, weeknum)
        if not weeknum:
            return
            #incorrectdate
        if studyweek:
            studyday = studyweek.get_day(date.weekday())
            return {
                "default_group": get_preferred_group_params(self.request),
                "studyday": studyday,
                "target_date": date,
                "weeknum": weeknum,
                "group": group,
                "subgroup": subgroup,
                "fetcheddate": pytz.utc.localize(group_data[DICTDATA_DATE_KEY_NAME]).astimezone(minsk_tz)
                }


    def get(self,date, group, subgroup):
        default_group = get_preferred_group_params(self.request) or {}
        if not group:
            group = default_group.get("group",None)
        if not subgroup:
            subgroup = default_group.get("subgroup",None)
        context = self.get_ajax_context(date, group, subgroup) or {}
        now = datetime.datetime.now(tz = pytz.utc).astimezone(minsk_tz)
        context.update({
                "default_group": get_preferred_group_params(self.request),
                "now_time": now
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
        logging.debug("Post params for dayschedule %s" % self.request.POST)
        context = self.get_ajax_context()
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
        week_num = self.request.get("week", None)
        subgroup = bsuirparser.subgroup2int(subgroup)
        week_num = bsuirparser.week2int(week_num)
        if not group: #main page
            self.redirect("/")
        else:
            groupdata = get_group_data(group)
            if not groupdata:
                path = os.path.join(os.path.dirname(__file__),
                                    'templates', 'erroratbsuir.html')
                self.response.out.write(template.render(path,
                                        {'group': group,
                                        "default_group": get_preferred_group_params(self.request)
                                        }))
                return
            study_week = groupdata[DICTDATA_SCHEDULE_KEY_NAME]
            if study_week:
                localised_date = pytz.utc.localize(groupdata["date"]).astimezone(minsk_tz)
                study_week = study_week.filter(subgroup, week_num)
                path = os.path.join(os.path.dirname(__file__),
                                    'templates', 'schedule.html')
                self.response.out.write(template.render(path, {"week": study_week,
                                        "group": group, "subgroup": subgroup,
                                        "selweek": week_num,
                                        "weeknumbers": range(1, 5),
                                        "default_group": get_preferred_group_params(self.request),
                "fetcheddate": localised_date,
                "current_week" : bsuirparser.get_week_num(localised_date.year, localised_date.month, localised_date.day)
                                        })
                                        )
            else:
                self.response.headers['Content-Type'] = 'text/plain'
                self.response.out.write(u"Что-то пошло не так")
                logging.debug(u"Ошибка при разборе расписания")


class StatPage(webapp2.RequestHandler):

    def get(self):
        def lecturers_cmp(a, b):
            """Опустить все пустые имена вниз"""
            if a[0] == b[0]:
                return 0
            if a[0] == "":
                return 1
            if b[0] == "":
                return -1
            return cmp(a,b)

        group = self.request.get("group", None)
        default_group = get_preferred_group_params(self.request)['group']
        if not group:
            group = default_group
        if not group:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write(u"Не указана группа")
            logging.debug(u"group param is None")
            return
        group_data = get_group_data(group)
        if not group_data:
            path = os.path.join(os.path.dirname(__file__),
                'templates', 'erroratbsuir.html')
            self.response.out.write(template.render(path,
                    {'group': group,
                     "default_group": get_preferred_group_params(self.request)
                }))
            return
        study_week = group_data[DICTDATA_SCHEDULE_KEY_NAME]
        places = study_week.get_places_list()
        lecturers_summary = study_week.get_lecturers_summary()
        lecturers_summary_list = lecturers_summary.items()
        lecturers_summary_list.sort(lecturers_cmp)
        subjects_stat = study_week.get_subjects_stat()
        # Нельзя корректно посчитать
        subjects_stat.pop(u"Спецподготовка", None)
        path = os.path.join(os.path.dirname(__file__),
            'templates', 'stats.html')
        self.response.out.write(template.render(path,
            {
            "default_group": get_preferred_group_params(self.request),
            "places": places,
            "lecturers_summary_list": lecturers_summary_list,
            "group": group,
            "subjects_stat": subjects_stat,
            }))

class NotFoundPage(webapp2.RequestHandler):


    def get(self):
        path = os.path.join(os.path.dirname(__file__),
                                    'templates', '404.html')
        self.response.out.write(template.render(path,
                                        {
                                        "default_group": get_preferred_group_params(self.request)
                                        }))

app = webapp2.WSGIApplication([
                                (r'/(home)?', MainPage),
                                (r'/weekschedule',GroupSchedulePage),
                                (r'/dayschedule(?:/([^/]*))?(?:/([^/]*))?(?:/([^/]*))?',DaySchedulePage), # O_o
                                (r'/stats', StatPage),
                                (r'/.*', NotFoundPage)

                                ])
