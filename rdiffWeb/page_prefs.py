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

from rdw_helpers import joinPaths
import rdw_helpers, page_main, librdiff
import os
import urllib
import rdw_spider_repos
import email_notification


class rdiffPreferencesPage(page_main.rdiffPage):
   
   sampleEmail = 'joe@example.com'
   
   def index(self, **parms):
      if parms:
         action = parms['form']
         if action == 'setPassword':
            return self._changePassword(parms['current'], parms['new'], parms['confirm'])
         elif action == 'updateRepos':
            return self._updateRepos()
         elif action == 'setNotifications':
            return self._setNotifications(parms)
         elif action == 'setRestoreType':
            return self._setRestoreType(parms['restoreType'])
         else:
            return self._getPrefsPage(errorMessage='Datos incorrectos.')
         
      return self._getPrefsPage('', '')
   index.exposed = True
   
   def _changePassword(self, currentPassword, newPassword, confirmPassword):
      if not self.getUserDB().modificationsSupported():
         return self._getPrefsPage(errorMessage="No puedes cambiar tu password.")
      
      if not self.getUserDB().areUserCredentialsValid(self.getUsername(), currentPassword):
         return self._getPrefsPage(errorMessage="El password actual no coincide")
      
      if newPassword != confirmPassword:
         return self._getPrefsPage(errorMessage="El nuevo password no coincide.")

      self.getUserDB().setUserPassword(self.getUsername(), newPassword)      
      return self._getPrefsPage(statusMessage="Password actualizado.")
   
   def _updateRepos(self):
      rdw_spider_repos.findReposForUser(self.getUsername(), self.getUserDB())
      return self._getPrefsPage(statusMessage="Carpetas actualizadas.")

   def _setNotifications(self, parms):
      if not self.getUserDB().modificationsSupported():
         return self._getPrefsPage(errorMessage="La notificacions por mial no esta activada")
      
      repos = self.getUserDB().getUserRepoPaths(self.getUsername())
      
      for parmName in parms.keys():
         if parmName == "userEmail":
            if parms[parmName] == self.sampleEmail:
               parms[parmName] = ''
            self.getUserDB().setUserEmail(self.getUsername(), parms[parmName])
         if parmName.endswith("numDays"):
            backupName = parmName[:-7]
            if backupName in repos:
               if parms[parmName] == "Don't notify":
                  maxDays = 0
               else:
                  maxDays = int(parms[parmName][0])
               self.getUserDB().setRepoMaxAge(self.getUsername(), backupName, maxDays)
               
      return self._getPrefsPage(statusMessage="Actualizados los datos.")
   
   def _setRestoreType(self, restoreType):
      if not self.getUserDB().modificationsSupported():
         return self.getPrefsPage(errorMessage="No se pueden cambiar los datos")
      
      if restoreType == 'zip' or restoreType == 'tgz':
         self.getUserDB().setUseZipFormat(self.getUsername(), restoreType == 'zip')
      else:
         return self._getPrefsPage(errorMessage='Formato invalido.')
      return self._getPrefsPage(statusMessage="Formatos actualizados.")
   
   def _getPrefsPage(self, errorMessage="", statusMessage=""):
      title = "Preferencias"
      email = self.getUserDB().getUserEmail(self.getUsername());
      parms = {
         "title" : title,
         "error" : errorMessage,
         "message" : statusMessage,
         "userEmail" : email,
         "notificationsEnabled" : False,
         "backups" : [],
         "useZipFormat": self.getUserDB().useZipFormat(self.getUsername()),
         "sampleEmail": self.sampleEmail
      }
      if email_notification.emailNotifier().notificationsEnabled():
         repos = self.getUserDB().getUserRepoPaths(self.getUsername())
         backups = []
         for repo in repos:
            maxAge = self.getUserDB().getRepoMaxAge(self.getUsername(), repo)
            notifyOptions = []
            for i in range(0, 8):
               notifyStr = "Don't notify"
               if i == 1:
                  notifyStr = "1 day"
               elif i > 1:
                  notifyStr = str(i) + " days"
                  
               selectedStr = ""
               if i == maxAge:
                  selectedStr = "selected"
               
               notifyOptions.append({ "optionStr": notifyStr, "selectedStr": selectedStr })
               
            backups.append({ "backupName" : repo, "notifyOptions" : notifyOptions })
         
         parms.update({ "notificationsEnabled" : True, "backups" : backups })
         
      return self.startPage(title) + self.compileTemplate("user_prefs.html", **parms) + self.endPage()
      

