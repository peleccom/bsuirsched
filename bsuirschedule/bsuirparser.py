#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import cookielib

from lxml import etree
import urllib
import urllib2
import logging
import datetime
import models
import json


def fetch(group):
    u'''Скачать HTML с расписанием с bsuir.
    Возвращает строку с html-разметкой таблицы или None'''
    try:
        parser = etree.HTMLParser(encoding="utf8")
        url = "http://www.bsuir.by/psched/schedulegroup?group=%s" % urllib.quote(group)
        raw_html = urllib.urlopen(url).read()
        root = etree.HTML(raw_html, parser=parser)
        table = root.xpath(".//*[@id='tableZone']/table")
        if table:
            return etree.tostring(table[0], encoding="unicode")
        else:
            return None
    except Exception, e:
        logging.error("Fetching error %s" % (str(e)))
        return None


def parse(tablestring):
    u'''Распарсить таблицу в объект StudyWeek'''
    root = etree.HTML(tablestring)
    table = root.xpath(".//table")
    if not table:
        return None
    table = table[0]
    days = table.xpath("//tr")
    days = days[1:]
    st_days = []
    for day in days:
        name = day.xpath("td[1]")[0]
        ##        print name.text
        weeks = [week.text for week in day.xpath("td[2]")[0]]
        ##        print weeks
        times = [time.text for time in day.xpath("td[3]")[0]]
        ##        print times
        subgroups = [subgroup.text for subgroup in day.xpath("td[4]")[0]]
        ##        print subgroups
        subjects = [subject.text for subject in day.xpath("td[5]")[0]]
        ##        print subjects
        lesson_types = [lessontype.text for lessontype in day.xpath("td[6]")[0]]
        ##        print lessontypes
        places = [place.text for place in day.xpath("td[7]")[0]]
        ##        print places
        lecturers = [lecturer.text for lecturer in day.xpath("td[8]")[0]]
        ##        print lecturers
        lessons = []
        for i in range(len(subjects)):
            les = models.Lesson(weeks[i], times[i], subgroups[i], subjects[i],
                lesson_types[i], places[i], lecturers[i])
            lessons.append(les)
        st_day = models.StudyDay(lessons, name.text)
        st_days.append(st_day)
    st_week = models.StudyWeek(st_days)
    return st_week


def get_week_num(year, month, day):
    """Return week number"""
    try:
        if month >= 9:
            startday = datetime.date(year, 9, 1)
        else:
            startday = datetime.date(year - 1, 9, 1)
        newweek = datetime.date(year, month, day).isocalendar()[1]
        startweek = startday.isocalendar()[1]
        return ((newweek - startweek) % 4) + 1
    except Exception:
        return None


def subgroup2int(subgroup_str):
    """Convert subgroup string to int with Value Error handling"""
    try:
        subgroup = int(subgroup_str)
        if not 1 <= subgroup <= 2:
            raise ValueError("Subgroup must be 1-2")
    except Exception, e:
        subgroup = None
    return subgroup


def week2int(week_str):
    """Convert week string to int with Value Error handling"""
    try:
        week = int(week_str)
        if not 1 <= week <= 4:
            raise ValueError("Week must be 1-4")
    except Exception, e:
        week = None
    return week


def get_groups_list():
    """Return list of groups from bsuir schedule page"""
    try:
        result_groups = []
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
        url = "http://www.bsuir.by/psched/schedulegroup.tab2_link"
        select_faculty_url = "http://www.bsuir.by/psched/schedulegroup.faculty:change"
        select_course_url = "http://www.bsuir.by/psched/schedulegroup.course:change"
        select_flow_url = "http://www.bsuir.by/psched/schedulegroup.flow:change"
        post_params = {
            "t:zoneid":"zoneFlow",
            "t:formid":"filterForm",
            "t:formcomponentid":"ScheduleGroup:filterform",
            "t:selectvalue":"34330000000000000000000000"
                    }
        headers = {'X-Prototype-Version':'1.7',
                   'X-Requested-With':'XMLHttpRequest'}
        faculties_list_request = urllib2.Request(url)
        raw_html = opener.open(faculties_list_request).read()
        parser = etree.HTMLParser(encoding="utf8")
        root = etree.HTML(raw_html, parser=parser)
        faculties = root.xpath(".//select[@id='faculty']/option")
        for faculty in faculties:
            ## перебираем факультеты
            #print faculty.text
            #установка параметра факультет
            post_params['t:selectvalue'] = faculty.attrib.get("value")
            #запрос факультет
            groups_list_request = urllib2.Request(select_faculty_url, urllib.urlencode(post_params), headers)
#            print post_params
            s_json_value = opener.open(groups_list_request).read()
            #получаем ответ в json
            try:
                json_value = json.loads(s_json_value)
                html = json_value['zones']['zoneCourse']
                courses_root = etree.HTML(html, parser=parser)
                options = courses_root.xpath(".//option")
                courses = [option.attrib.get("value") for option in options]
                for course in courses:
                    #print "\tcourse=", course
                    post_params["t:selectvalue"] = course
                    #запрос курса
                    groups_list_request = urllib2.Request(select_course_url, urllib.urlencode(post_params), headers)
#                    print post_params
                    s_json_value = opener.open(groups_list_request).read()
                    json_value_flow =  json.loads(s_json_value)
                    html = json_value_flow['zones']['zoneFlow']
                    courses_root = etree.HTML(html, parser=parser)
                    options = courses_root.xpath(".//option")
                    flows = [option.attrib.get("value") for option in options]
                    for flow in flows:
                        #print "\t\tflow=",flow
                        post_params["t:selectvalue"] = flow
                        #запрос курса
                        groups_list_request = urllib2.Request(select_flow_url, urllib.urlencode(post_params), headers)
                        #                    print post_params
                        s_json_value = opener.open(groups_list_request).read()
                        json_value_flow =  json.loads(s_json_value)
                        html = json_value_flow['zones']['zoneGroup']
                        groups_root = etree.HTML(html, parser=parser)
                        group_options = groups_root.xpath(".//option")
                        groups  = [group_option.text for group_option in  group_options]
                        for group in groups:
                            #print "\t\t\tgroup=", group
                            result_groups.append(group)
            except ValueError, e:
                logging.error(e)
        return result_groups
    except Exception, e:
        logging.error("Fetching groups error %s" % (str(e)))
        return None