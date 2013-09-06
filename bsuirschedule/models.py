#!/usr/bin/env python
# -*- coding: UTF-8 -*-


class LessonType(object):
    """Represent lesson type"""
    LEC = 1
    LAB = 2
    PR = 3
    NO_TYPE = 4

    def __init__(self, lesson_type):
        if isinstance(lesson_type, basestring):
            if lesson_type == u'лр':
                self._value = self.LAB
            elif lesson_type == u'пз':
                self._value = self.PR
            elif lesson_type == u'лк':
                self._value = self.LEC
            else:
                self._value = self.NO_TYPE
        elif (isinstance(lesson_type, int)) and (1 <= lesson_type <= 4):
            self._value = lesson_type
        else:
            self._value = self.NO_TYPE

    def is_lab(self):
        return self._value == self.LAB

    def is_pr(self):
        return self._value == self.PR

    def is_lec(self):
        return self._value == self.LEC

    def __eq__(self, other):
        return self._value == other._value

    def __ne__(self, other):
        return not(self.__eq__(other))


class Lesson(object):

    def __init__(self, weeks, time, subgroup, subject, lessontype, place, lecturer):
        """
        weeks - list of weeks. [1,2]
        time - time
        subgroup - number of subgroup
        subject - subject
        lessontype 'lec' 'pr' 'lab'
        place place
        lecturer lecturer
        """
        if not weeks:
            self._weeks = None
        else:
            self._weeks = []
            if isinstance(weeks, basestring):
                try:
                    self._weeks = [int(week)for week in weeks.strip().split(",")]
                except ValueError:
                    raise ValueError("Wrong week string %s" % weeks)
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

        self._lesson_type = lessontype

        self._place = place

        self._lecturer = lecturer

    def get_weeks_str(self):
        if not self._weeks:
            return u""
        return u",".join(str(i) for i in self._weeks)

    def get_weeks(self):
        return self._weeks

    def get_subgroup_str(self):
        s = self._subgroup
        if s:
            return str(s)
        else:
            return u""

    def get_subgroup(self):
        return self._subgroup

    def get_subject_str(self):
        subject = self._subject
        if subject:
            return subject
        else:
            return u""

    def get_lecturer_str(self):
        lecturer = self._lecturer
        if lecturer:
            return lecturer
        else:
            return u""

    def get_lesson_type_str(self):
        lessontype = self._lesson_type
        if lessontype:
            return lessontype
        else:
            return u""

    def get_lesson_type_object(self):
        """
        Return LessonType enumeration value
        """
        return LessonType(self._lesson_type)

    def get_place_str(self):
        place = self._place
        if place:
            return place
        else:
            return u""

    def get_time_str(self):
        time = self._time
        if time:
            return time
        else:
            return u""

    def __unicode__(self):
        loc = {
            "weeks": self.get_weeks_str(),
            "time": self.get_time_str(),
            "subgroup": self.get_subgroup_str(),
            "subject": self.get_subject_str(),
            "lessontype": self.get_lesson_type_str(),
            "place": self.get_place_str(),
            "lecturer": self.get_lecturer_str()
        }
        return u'''%(weeks)s  %(time)s %(subgroup)s %(subject)s %(lessontype)s %(place)s %(lecturer)s''' % loc


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
        """
        Filter by subgroup or/and week
        """
        if not subgroup and not week:
            return self
        new_lessons_0 = []
        new_lessons = []
        if subgroup:
            for lesson in self:
                sb = lesson.get_subgroup_str()
                if not sb or sb == subgroup:
                    new_lessons_0.append(lesson)
        else:
            new_lessons_0 = [lesson for lesson in self]
        if week:
            for lesson in new_lessons_0:
                wk = lesson._weeks
                if not wk or week in wk:
                    new_lessons.append(lesson)
        else:
            new_lessons = new_lessons_0
        return StudyDay(new_lessons, self._name)

    def get_name(self):
        return self._name

    def get_full_name(self):
        weekday_names = {
            u"пн": u"Понедельник",
            u"вт": u"Вторник",
            u"ср": u"Среда",
            u"чт": u"Четверг",
            u"пт": u"Пятница",
            u"сб": u"Суббота",
            u"вс": u"Воскресенье"
        }

        return weekday_names.get(self.get_name(), None)


class StudyWeek(object):

    def __init__(self, studydays):
        self._studydays = []
        for studyday in studydays:
            self._studydays.append(studyday)

    def __iter__(self):
        return iter(self._studydays)

    def filter(self, subgroup, week=None):
        days = []
        for day in self:
            days.append(day.filter(subgroup, week))
        return StudyWeek(days)

    def get_lecturer_list(self, lesson_type=None):
        lecturers_set = set()
        for study_day in self._studydays:
            for lesson in study_day:
                if lesson_type:
                    if lesson_type != lesson.get_lesson_type_object():
                        continue
                lecturer = lesson.get_lecturer_str()
                if lecturer:
                    lecturers_set.add(lecturer)
        return list(lecturers_set)

    def get_subject_list(self, lesson_type=None):
        subjects_set = set()
        for study_day in self._studydays:
            for lesson in study_day:
                if lesson_type:
                    if lesson_type != lesson.get_lesson_type_object():
                        continue
                subjects_set.add(lesson.get_subject_str())
        return list(subjects_set)

    def get_places_list(self, lesson_type=None):
        places_set = set()
        for study_day in self._studydays:
            for lesson in study_day:
                if lesson_type:
                    if lesson_type != lesson.get_lesson_type_object():
                        continue
                place = lesson.get_place_str()
                if place:
                    places_set.add(place)
        return list(places_set)

    def get_lecturers_summary(self):
        u"""
        Возвращает dict где ключи lecturers, следующего вида
        {
            lecturer1:  {
                            subject1: [lesson_type_str1, lesson_type_str2]
                        }
        }
        """
        lecturers_summary = {}
        for study_day in self._studydays:
            for lesson in study_day:
                lecturer = lesson.get_lecturer_str()
                subject = lesson.get_subject_str()
                lesson_type_str = lesson.get_lesson_type_str()
                if lecturers_summary.has_key(lecturer):
                    # преподаватель уже ведет что-то
                    subjects_dict = lecturers_summary.get(lecturer)
                    if subjects_dict.has_key(subject):
                        #присутствует и данный предмет
                        #возможно отсутствует данный тип предмета
                        lesson_type_list = subjects_dict.get(subject)
                        if lesson_type_str in lesson_type_list:
                            # уже занесено - к следующей итерации
                            continue
                        else:
                            lesson_type_list.append(lesson_type_str)
                    else:
                        subjects_dict[subject] = [lesson_type_str,]
                else:
                    lecturers_summary[lecturer] = {subject : [lesson_type_str]}
        return lecturers_summary

    def get_subjects_stat(self):
        """словарь с предметами и количеством занятий в неделю"""
        subjects_stat = {}
        for study_day in self._studydays:
            for lesson in study_day:
                subgroup = lesson.get_subgroup_str()
                # считаем по первой группе
                if subgroup and subgroup == 2:
                    continue
                subject_str = lesson.get_subject_str()
                weeks = lesson.get_weeks()
                # коэф. кол-ва занятий за 4 недели
                rate = 1
                if weeks:
                    if len(weeks):
                        rate = len(weeks)
                else:
                    rate = 4
                count = subjects_stat.get(subject_str,0)+rate
                subjects_stat[subject_str] = count
        return subjects_stat

    def get_day(self, day):
        """
        Return Studyday by number
        """
        try:
            return self._studydays[day]
        except IndexError:
            return None

    def __unicode__(self):
        s = u""
        for day in self:
            s += unicode(day) + "\n"
        return s