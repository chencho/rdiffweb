#!/usr/bin/python
# rdiffWeb, A web interface to rdiff-backup repositories
# Copyright (C) 2012 rdiffWeb contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import rdw_helpers
import page_main
import rdw_templating
import cherrypy
import rdw_spider_repos


class rdiffAdminPage(page_main.rdiffPage):
   def index(self, **kwargs):
      if not self._userIsAdmin(): return self.writeErrorPage("Acceso denegado.")
      
      # If we're just showing the initial page, just do that
      if not self._isSubmit():
         return self._generatePageHtml("", "")
      
      # We need to change values. Change them, then give back that main page again, with a message
      action = cherrypy.request.params["action"]
      username = cherrypy.request.params["username"]
      userRoot = cherrypy.request.params["userRoot"]
      userIsAdmin = cherrypy.request.params.get("isAdmin", False) != False
      
      if action == "edit":
         if not self.getUserDB().userExists(username):
            return self._generatePageHtml("", "El usuario no existe.")
         
         self.getUserDB().setUserInfo(username, userRoot, userIsAdmin)
         return self._generatePageHtml("Informacion modificada correctamente", "")
      elif action == "add":
         if self.getUserDB().userExists(username):
            return self._generatePageHtml("", "El usuario ya existe.", username, userRoot, userIsAdmin)
         if username == "":
            return self._generatePageHtml("", "El usuario no es valido.", username, userRoot, userIsAdmin)
         self.getUserDB().addUser(username)
         self.getUserDB().setUserPassword(username, cherrypy.request.params["password"])
         self.getUserDB().setUserInfo(username, userRoot, userIsAdmin)
         return self._generatePageHtml("Usuario incluido correctamente.", "")
      
   index.exposed = True

   def deleteUser(self, user):
      if not self._userIsAdmin(): return self.writeErrorPage("Acceso denegado.")

      if not self.getUserDB().userExists(user):
         return self._generatePageHtml("", "El usuario no existe.")

      if user == self.getUsername():
         return self._generatePageHtml("", "No puedes eliminar tu cuenta!.")

      self.getUserDB().deleteUser(user)
      return self._generatePageHtml("Usuario eliminado.", "")
   deleteUser.exposed = True

   ############### HELPER FUNCTIONS #####################
   def _userIsAdmin(self):
      return self.getUserDB().userIsAdmin(self.getUsername())

   def _isSubmit(self):
      return cherrypy.request.method == "POST"

   def _generatePageHtml(self, message, error, username="", userRoot="", isAdmin=False):
      userNames = self.getUserDB().getUserList()
      users = [ { "username" : user, "isAdmin" : self.getUserDB().userIsAdmin(user), "userRoot" : self.getUserDB().getUserRoot(user) } for user in userNames ]
      parms = { "users" : users,
                "username" : username,
                "userRoot" : userRoot,
                "isAdmin" : isAdmin,
                "message" : message,
                "error" : error }
      return self.startPage("Administracion") + self.compileTemplate("admin_main.html", **parms) + self.endPage()

