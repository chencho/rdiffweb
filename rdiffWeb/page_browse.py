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

from rdw_helpers import joinPaths, encodePath
import rdw_helpers, page_main, librdiff
import os
import urllib


class rdiffBrowsePage(page_main.rdiffPage):
   
   def index(self, repo="", path="", restore=""):
      try:
         self.validateUserPath(joinPaths(repo, path))
      except rdw_helpers.accessDeniedError, error:
         return self.writeErrorPage(str(error))

      # NOTE: a blank path parm is allowed, since that just results in a listing of the repo root
      if not repo: return self.writeErrorPage("Directorio no especificado.")
      if not repo in self.getUserDB().getUserRepoPaths(self.getUsername()):
         return self.writeErrorPage("Acceso denegado.")

      try:
         parms = self.getParmsForPage(self.getUserDB().getUserRoot(self.getUsername()), repo, path, restore)
      except librdiff.FileError, error:
         return self.writeErrorPage(str(error))
      page = self.startPage(parms["title"])
      page = page + self.compileTemplate("dir_listing.html", **parms)
      page = page + self.endPage()
      return page
   
   index.exposed = True
   
   
   def getParmsForPage(self, userRoot, repo="", path="", restore=""):
      repo = encodePath(repo)
      path = encodePath(path)
      # Build "parent directories" links
      parentDirs = []
      parentDirs.append({ "parentPath" : self.buildBrowseUrl(repo, "/", False), "parentDir" : repo.lstrip("/") })
      parentDirPath = "/"
      for parentDir in path.split("/"):
         if parentDir:
            parentDirPath = joinPaths(parentDirPath, parentDir)
            parentDirs.append({ "parentPath" : self.buildBrowseUrl(repo, parentDirPath, False), "parentDir" : parentDir })
      parentDirs[-1]["parentPath"] = "" # Clear link for last parent, so it doesn't show it as a link

      # Set up warning about in-progress backups, if necessary
      if librdiff.backupIsInProgressForRepo(joinPaths(userRoot, repo)):
         backupWarning = "Atencion: una copia se esta ejecutando ahora mismo. Los datos pueden no ser consistentes."
      else:
         backupWarning = ""

      restoreUrl = ""
      viewUrl = ""
      if restore == "T":
         title = "Restore"
         viewUrl = self.buildBrowseUrl(repo, path, False)
         tempDates = librdiff.getDirRestoreDates(joinPaths(userRoot, repo), path)
         tempDates.reverse() # sort latest first
         restoreDates = []
         for x in tempDates:
            restoreDates.append({ "dateStr" : x.getDisplayString(),
                                 "dirRestoreUrl" : self.buildRestoreUrl(repo, path, x) })
         entries = []
      else:
         title = "Browse"
         restoreUrl = self.buildBrowseUrl(repo, path, True)
         restoreDates = []

         # Get list of actual directory entries
         fullRepoPath = joinPaths(userRoot, repo)
         libEntries = librdiff.getDirEntries(fullRepoPath, path)

         entries = []
         for libEntry in libEntries:
            entryLink = ""
            if libEntry.isDir:
               entryLink = self.buildBrowseUrl(repo, joinPaths(path, libEntry.name), False)
               fileType = "folder"
               size = " "
               sizeinbytes = 0
               changeDates = []
            else:
               entryLink = self.buildRestoreUrl(repo, joinPaths(path, libEntry.name), libEntry.changeDates[-1])
               fileType = "file"
               entryChangeDates = libEntry.changeDates[:-1]
               entryChangeDates.reverse()
               size = rdw_helpers.formatFileSizeStr(libEntry.fileSize)
               sizeinbytes = libEntry.fileSize
               changeDates = [ { "changeDateUrl" : self.buildRestoreUrl(repo, joinPaths(path, libEntry.name), x),
                                 "changeDateStr" : x.getDisplayString() } for x in entryChangeDates]

            showRevisionsText = (len(changeDates) > 0) or libEntry.isDir
            entries.append({ "filename" : libEntry.name,
                           "fileRestoreUrl" : entryLink,
                           "filetype" : fileType,
                           "exists" : libEntry.exists,
                           "date" : libEntry.changeDates[-1].getDisplayString(),
                           "dateinseconds" : libEntry.changeDates[-1].getLocalSeconds(),
                           "size" : size,
                           "sizeinbytes" : sizeinbytes,
                           "hasPrevRevisions" : len(changeDates) > 0,
                           "numPrevRevisions" : str(len(changeDates)),
                           "hasMultipleRevisions" : len(changeDates) > 1,
                           "showRevisionsText" : showRevisionsText,
                           "changeDates" : changeDates})

      return { "title" : title, "files" : entries, "parentDirs" : parentDirs, "restoreUrl" : restoreUrl, "viewUrl" : viewUrl, "restoreDates" : restoreDates, "warning" : backupWarning }

class browsePageTest(page_main.pageTest, rdiffBrowsePage):
   def getTemplateName(self):
      return "browse_template.txt"
   
   def getExpectedResultsName(self):
      return "browse_results.txt"
      
   def getParmsForTemplate(self, repoParentPath, repoName):
      return self.getParmsForPage(repoParentPath, repoName)
