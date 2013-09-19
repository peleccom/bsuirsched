# -*- coding: UTF-8 -*-

import webapp2
import logging
from bsuirschedule import bsuirparser
from models import GroupsList
from models import  GroupSchedule

class UpdateGroupsListPage(webapp2.RequestHandler):
    def get(self):
        groups = bsuirparser.get_groups_list()
        if groups:
            old_value = GroupsList.query().get()
            if old_value:
                old_value.key.delete()
            GroupsList(groups_list = groups).put()
            self.response.out.write("%s" % groups)
            logging.info("Task update_groups_list successfully ended")
        else:
            logging.error("Task update_groups_list failed")
            self.response.out.write("fail")
        return

class DeleteInvalidGroupsPage(webapp2.RequestHandler):
    def get(self):
        groupsList = GroupsList.query().get()
        if not groupsList:
            self.error(404)
            return
        groups = groupsList.groups_list
        for group_schedule in GroupSchedule.query():
            if not group_schedule.group in groups:
                logging.debug(u"Deleting invalid group %s"%group_schedule.group)
                group_schedule.key.delete()
        logging.info("Task delete_invalid_groups successfully ended")


app = webapp2.WSGIApplication([
    ('/tasks/update_groups_list', UpdateGroupsListPage),
    ('/tasks/delete_invalid_groups', DeleteInvalidGroupsPage),

])
