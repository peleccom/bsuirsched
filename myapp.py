# -*- coding: UTF-8 -*-
import webapp2
import os
from google.appengine.ext.webapp import template
from bsuirschedule import bsuirparser


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
            parsed = bsuirparser.parse(group, subgroup, week)
            if parsed:
                path = os.path.join(os.path.dirname(__file__),
                                'templates', 'schedule.html')
                self.response.out.write(template.render(path, {"week": parsed,
                                        "group": group, "subgroup": subgroup,
                                        "weeknumbers": range(1,5)})
                                        )
            else:
                self.response.headers['Content-Type'] = 'text/plain'
                self.response.out.write(u"Нет расписания")

app = webapp2.WSGIApplication([('/', MainPage)])
