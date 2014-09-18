#! /usr/bin/env python
#
#  term-peeper is a program for classifying MODIS imagery of glacier termini
#  this file is part of term-peeper
#
#  Copyright 2014 Logan C Byers
#
#  Authors: Logan C Byers
#  Contact: loganbyers@ku.edu
#  Date: 2014.09.18
#  Modified: 2014.09.18
#
###############################################################################
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#
###############################################################################
#

import os
from PyQt4 import QtGui, uic
import pymodis

### WINDOWS AND DIALOGS ###

class DownloadMODISDialog(QtGui.QDialog):
    """Dialog for selecting and downloading MODIS scenes"""
  
    def __init__(self,parent=None):
        """Initialize dialog and show it
        
        Parameters
        ----------
        
        parent : QtGui.QDialog
            A parent to inherit from
        
        
        Post
        ----
        
        If user inputs data and accepts, MODIS scenes are downloaded
        into the chosen directory.
        
        """
        ## UI GEOMETRY AND SETUP##
        super(DownloadMODISDialog,self).__init__(parent)
        uic.loadUi("ui/data_download_dialog.ui",self)
        self.show()
        self.tilesLineEdit.setText("h16v01")
        
        ## SIGNAL CONNECTIONS ##
        self.saveDirectoryToolButton.clicked.connect(self.slotSaveDirectoryToolButton)
        self.startDateCalendar.selectionChanged.connect(self.slotStartDateSelectionChanged)
        self.endDateCalendar.selectionChanged.connect(self.slotEndDateSelectionChanged)
        self.buttonBox.accepted.connect(self.slotAccepted)
        self.buttonBox.rejected.connect(self.slotRejected)
        

        ## PUBLIC MEMBER VARIABLES ##
        self.downloadDirectory = None
        self.downloadTile = None
        self.startDate = None
        self.endDate = None
    
    ### SLOT DEFINITIONS ###
    def slotSaveDirectoryToolButton(self):
        """Runs a file dialog to choose a directory"""
        print ("Opening MODIS Save Directory Dialog")
        self.saveDirectoryLineEdit.setText(QtGui.QFileDialog.getExistingDirectory())
        pass
      
    def slotStartDateSelectionChanged(self):
        """Updates the start date of image acquisition"""
        print ("Changed Start Date Selection")
        self.startDate = str(self.startDateCalendar.selectedDate().toString("yyyy-MM-dd"))
        pass
    
    def slotEndDateSelectionChanged(self):
        """Updates the end date of image acquisition"""
        print ("Changed End Date Selection")
        self.endDate = str(self.endDateCalendar.selectedDate().toString("yyyy-MM-dd"))
        pass
    
    def slotAccepted(self):
        """Stores data from user fields and downloads as specified
        
        Post
        ----
        
        Member variables are updated to user's values.
        Chosen data is downloaded to the image directory
        
        """
        print ("Accepted; starting to download")
        self.downloadDirectory = str(self.saveDirectoryLineEdit.text())
        if not self.downloadDirectory[-1] == os.path.sep:
            self.downloadDirectory = self.downloadDirectory+os.path.sep
        self.tiles = str(self.tilesLineEdit.text())
        self.startDate = str(self.startDateCalendar.selectedDate().toString("yyyy-MM-dd"))
        self.endDate = str(self.endDateCalendar.selectedDate().toString("yyyy-MM-dd"))
        print self.downloadDirectory
        print self.tiles
        print self.startDate
        print self.endDate
        self.downloadData()
        pass
    
    def slotRejected(self):
        """Cleans up when dialog is quit without downloading"""
        print ("Rejected; exiting dialog")
        pass
    

    ### DOWNLOADING ###
    def downloadData(self):
        """Download data to local directory"""
        if not os.path.exists(self.downloadDirectory):
            os.mkdir(self.downloadDirectory)
        #start and end seem reversed, but that is how pymodis works --backwards
        dm = pymodis.downmodis.downModis(destinationFolder=self.downloadDirectory,
                                         path="MOLT", product="MOD09GA.005",
                                         tiles="h16v01", today=self.endDate,
                                         enddate = self.startDate)
        dm.connect()
        print "Connection Attempts: " + str(dm.nconnection)
        
        #get all files to download, for each day of interest
        downloads = []
        for day in dm.getListDays():
            print day
            files = dm.getFilesList(day)
            print files
            for f in files:
                downloads.append((f,day))
        numDownload = len(downloads)
        print  "Files to Download: " + str(numDownload)
        
        self.progress = QtGui.QProgressBar()
        self.progress.setRange(0,numDownload)
        self.progress.setValue(0)
        self.progress.show()
        for f, d in downloads:
            print "DL: " + f
            self.progress.setValue(self.progress.value()+1)
            dm.downloadFile(f,self.downloadDirectory+f,d)
        