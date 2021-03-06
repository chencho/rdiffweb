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

import os
import db
import rdw_helpers
import librdiff
import rdw_config
import time
import threading

# Returns pid of started process, or 0 if no process was started
def startRepoSpiderThread(killEvent):
   newThread = spiderReposThread(killEvent)
   newThread.start()

class spiderReposThread(threading.Thread):
   def __init__(self, killEvent):
      self.killEvent = killEvent
      threading.Thread.__init__(self)
      
   def run(self):
      spiderInterval = rdw_config.getConfigSetting("autoUpdateRepos")
      if spiderInterval:
         spiderInterval = int(spiderInterval)         
         while True:
            findReposForAllUsers()
            self.killEvent.wait(60 * spiderInterval)
            if self.killEvent.isSet():
               return
      

def _findRdiffRepos(dirToSearch, outRepoPaths):
   dirEntries = os.listdir(dirToSearch)
   if librdiff.rdiffDataDirName in dirEntries:
      outRepoPaths.append(dirToSearch)
      return

   for entry in dirEntries:
      entryPath = rdw_helpers.joinPaths(dirToSearch, entry)
      if os.path.isdir(entryPath) and not os.path.islink(entryPath):
         _findRdiffRepos(entryPath, outRepoPaths)


def findReposForUser(user, userDBModule):
   userRoot = userDBModule.getUserRoot(user)
   repoPaths = []
   _findRdiffRepos(userRoot, repoPaths)

   def stripRoot(path):
      if not path[len(userRoot):]:
         return "/"
      return path[len(userRoot):]
   repoPaths = map(stripRoot, repoPaths)
   userDBModule.setUserRepos(user, repoPaths)


def findReposForAllUsers():
   userDBModule = db.userDB().getUserDBModule()
   if not userDBModule.modificationsSupported(): return
   
   users = userDBModule.getUserList()
   for user in users:
      findReposForUser(user, userDBModule)

