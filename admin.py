# -*- coding: UTF-8 -*-
import os
import logging

import webapp2
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from models import GroupSchedule

def erasedata(group):
    u'''Erase group schedule from cache and DB'''
    group = str(group)
    memcache.delete(group)
    q = GroupSchedule.all()
    q.filter("group = ", group)
    results = q.fetch(1)
    if results:
        results[0].delete()


class AdminPage(webapp2.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__),
                                'templates', 'indexadmin.html')
        self.response.out.write(template.render(path, {}))
        return

class EraseDataPage(webapp2.RequestHandler):
    def post(self):
                self.response.headers['Content-Type'] = 'text/plain'
                group = self.request.get("group", None)
                if not group:
                    self.response.out.write(u"Fail")
                else:
                    erasedata(group)
                    self.response.out.write(u"OK")
                return


app = webapp2.WSGIApplication([
                                ('/admin', AdminPage),
                                ('/admin/erasedata',EraseDataPage)

                                ])
