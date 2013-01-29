#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from lxml import etree
import models
import urllib
import urllib2
import logging

import os.path


def fetch(group):
    u'''Скачать HTML с расписанием с bsuir'''
    try:
        parser = etree.HTMLParser(encoding="utf8")
        url = "http://www.bsuir.by/psched/schedulegroup?group=%s" % group
        #url = "http://127.0.0.1:8000/%s.htm" % group

        rawhtml = urllib.urlopen(url).read()
        root = etree.HTML(rawhtml, parser=parser)
        table = root.xpath(".//*[@id='tableZone']/table")
        if table:
            return etree.tostring(table[0], encoding="unicode")
        else:
            return None
    except Exception, e:
        logging.info("Fetching group %s error %s" %(str(group),str(e)))
        return None


def parse(tablestring, needsubgroup=None, needweek=None):
    '''Распарсить таблицу в объект StudyWeek'''
    root = etree.HTML(tablestring)
    table = root.xpath(".//table")
    if not table:
        return None
    if needsubgroup:
        try:
            needsubgroup = int(needsubgroup)
        except ValueError, e:
            return None
    if needweek:
        try:
            needweek = int(needweek)
        except ValueError, e:
            logging.debug("Exception in bsuirparser.parse %s" % str(e))
            return None

    table = table[0]
    days = table.xpath("//tr")
    days = days[1:]
    stweek = []
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
        lessontypes = [lessontype.text for lessontype in day.xpath("td[6]")[0]]
##        print lessontypes
        places = [place.text for place in day.xpath("td[7]")[0]]
##        print places
        lecturers = [lecturer.text for lecturer in day.xpath("td[8]")[0]]
##        print lecturers
        lessons = []
        for i in range(len(subjects)):

            les = models.Lesson(weeks[i], times[i], subgroups[i], subjects[i],
                                lessontypes[i], places[i], lecturers[i])
            lessons.append(les)
        stday = models.StudyDay(lessons, name.text)
        stweek.append(stday)
    stweek = models.StudyWeek(stweek)
    return (stweek.filter(needsubgroup, needweek))
