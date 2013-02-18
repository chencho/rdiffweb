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

from cherrypy.lib.static import serve_file, serve_download
import rdw_helpers, page_main, librdiff
import os


class autoDeleteDir:
   def __init__(self, dirPath):
      self.dirPath = dirPath

   def __del__(self):
      rdw_helpers.removeDir(self.dirPath)

class rdiffRestorePage(page_main.rdiffPage):
   _cp_config = {"response.stream": True, "response.timeout": 3000 }
   
   def index(self, repo, path, date):
      try:
         self.validateUserPath(rdw_helpers.joinPaths(repo, path))
      except rdw_helpers.accessDeniedError, error:
         return self.writeErrorPage(str(error))
      if not repo: return self.writeErrorPage("Carpeta de copia no especificada.")
      if not repo in self.getUserDB().getUserRepoPaths(self.getUsername()):
         return self.writeErrorPage("Acceso denegado.")

      if librdiff.backupIsInProgressForRepo(rdw_helpers.joinPaths(self.getUserDB().getUserRoot(self.getUsername()), repo)):
         return self.writeErrorPage("Una copia se esta ejecutando.  La restauracion esta deshabilitada hasta que esta termine.")

      try:
         restoreTime = rdw_helpers.rdwTime()
         restoreTime.initFromString(date)
         (path, file) = os.path.split(path)
         if not file:
            file = path
            path = "/"
         fullPath = rdw_helpers.joinPaths(self.getUserDB().getUserRoot(self.getUsername()), repo)
         useZipFormat = self.getUserDB().useZipFormat(self.getUsername())
         filePath = librdiff.restoreFileOrDir(fullPath, path, file, restoreTime, useZipFormat)
      except librdiff.FileError, error:
         return self.writeErrorPage(error.getErrorString())
      except ValueError:
         return self.writeErrorPage("Fecha invalida.")

      (directory, filename) = os.path.split(filePath)
      filename = filename.replace("\"", "\\\"") # Escape quotes in filename
      return serve_file(filePath, None, disposition="attachment", name=filename)
   index.exposed = True

