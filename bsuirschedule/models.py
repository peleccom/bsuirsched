#!/usr/bin/env python
# -*- coding: UTF-8 -*-

class Lesson(object):
    def __init__(self, weeks, time, subgroup, subject, lessontype, place, lecturer):
        '''
        weeks - list of weeks. [1,2]
        time - time
        subgroup - number of subgroup
        subject - subject
        lessontype 'lec' 'pr' 'lab'
        place place
        lecturer lecturer
        '''
        if not weeks:
            self._weeks = None
        else:
            self._weeks = []
            if isinstance(weeks, basestring):
                try:
                    self._weeks = [int(week)for week in weeks.strip().split(",")]
                except:
                    ValueError("Wrong week string %s" % weeks)
            else:
                try:
                    for week in weeks:
                        iweek = int(week)
                        if iweek in [1, 2, 3, 4]:
                            self._weeks.append(iweek)
                except:
                    raise ValueError("Weeks must be list of numbers")
        self._time = time
        if not subgroup:
            self._subgroup = None
        else:
            try:
                self._subgroup = int(subgroup)
            except:
                raise ValueError("Subgroup must be number")

        self._subject = subject

        self._lessontype = lessontype

        self._place = place

        self._lecturer = lecturer

    def getweeks(self):
        if not self._weeks:
            return ""
        return ",".join(str(i) for i in self._weeks)

    def getsubgroup(self):
        s = self._subgroup
        if s:
            return s
        else:
            return ""

    def getsubject(self):
        subject = self._subject
        if subject:
            return subject
        else:
            return ""

    def getlecturer(self):
        lecturer = self._lecturer
        if lecturer:
            return lecturer
        else:
            return ""

    def getlessontype(self):
##        slessontypes = {
##                            "lec" : u"Лекция",
##                            "lab" : u"Лабораторная",
##                            "pr"  : u"Практическая"
##                        }
##        slessontype = slessontypes[self._lessontype]
##        return slessontype
        lessontype = self._lessontype
        if lessontype:
            return lessontype
        else:
            return ""

    def getplace(self):
        place = self._place
        if place:
            return place
        else:
            return ""

    def gettime(self):
        time = self._time
        if time:
            return time
        else:
            return ""

    def __unicode__(self):
        loc = {
        "weeks": self.getweeks(),
        "time": self.gettime(),
        "subgroup": self.getsubgroup(),
        "subject": self.getsubject(),
        "lessontype": self.getlessontype(),
        "place": self.getplace(),
        "lecturer": self.getlecturer()
        }
        return u'''%(weeks)s  %(time)s %(subgroup)s %(subject)s %(lessontype)s %(place)s %(lecturer)s''' % (loc)


class StudyDay(object):
    def __init__(self, lessons, name):
        self.lessons = []
        for lesson in lessons:
            self.lessons.append(lesson)
        self._name = name

    def __iter__(self):
        return iter(self.lessons)

    def __unicode__(self):
        s = u"%s:\n" % self._name
        for les in self:
            s += unicode(les) + "\n"
        return s

    def filter(self, subgroup, week=None):
        '''Filter by subgroup'''
        if not subgroup and not week:
            return self
        newlessons0 = []
        newlessons = []
        if subgroup:
            for lesson in self:
                sb = lesson.getsubgroup()
                # print wk, week
                if not sb or sb == subgroup :
                    newlessons0.append(lesson)
        else:
            newlessons0=[lesson for lesson in self]
        if week:
            for lesson in newlessons0:
                wk = lesson._weeks
                if not wk or week in wk:
                    newlessons.append(lesson)
        else:
            newlessons = newlessons0


        return StudyDay(newlessons, self._name)

    def getname(self):
        return self._name

    def getFullName(self):
        weekday_names = {
        u"пн": u"Понедельник",
        u"вт":u"Вторник",
        u"ср":u"Среда",
        u"чт":u"Четверг",
        u"пт":u"Пятница",
        u"сб":u"Суббота",
        u"вс":u"Воскресенье"
        }

        return weekday_names.get(self.getname(),None)


class StudyWeek(object):
    def __init__(self, studydays):
        self.studydays = []
        for studyday in studydays:
            self.studydays.append(studyday)

    def __iter__(self):
        return iter(self.studydays)

    def filter(self, subgroup, week=None):
        days = []
        for day in self:
            days.append(day.filter(subgroup, week))
        return StudyWeek(days)

    def getDay(self, day):
        '''Return Studyday with number'''
        if day>5:
            return None
        return self.studydays[day]

    def __unicode__(self):
        s = u""
        for day in self:
            s += unicode(day) + "\n"
        return s

