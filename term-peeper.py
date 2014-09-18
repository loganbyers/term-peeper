#! /usr/bin/env python
#
#  term-peeper is a program for classifying MODIS imagery of glacier termini
#  this file is part of term-peeper
#
#  Copyright 2014 Logan C Byers
#
#  Authors: Logan C Byers
#  Contact: loganbyers@ku.edu
#  Date: 2014.08.28
#  Modified: 2014.09.17
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
# 
import sys
import os
import pickle
from PyQt4 import QtCore, QtGui, uic
import pymodis
#import numpy as np


class DownloadMODISDialog(QtGui.QDialog):
  
    def __init__(self,parent=None):
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
        print ("Opening MODIS Save Directory Dialog")
        self.saveDirectoryLineEdit.setText(QtGui.QFileDialog.getExistingDirectory())
        pass
      
    def slotStartDateSelectionChanged(self):
        print ("Changed Start Date Selection")
        self.startDate = str(self.startDateCalendar.selectedDate().toString("yyyy-MM-dd"))
        pass
    
    def slotEndDateSelectionChanged(self):
        print ("Changed End Date Selection")
        self.endDate = str(self.endDateCalendar.selectedDate().toString("yyyy-MM-dd"))
        pass
    
    def slotAccepted(self):
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
        print ("Rejected; exiting dialog")
        pass
    

    ### DOWNLOADING ###
    def downloadData(self):
        if not os.path.exists(self.downloadDirectory):
            os.mkdir(self.downloadDirectory)
        #start and end seem reversed, but that is how pymodis works --backwards
        dm = pymodis.downmodis.downModis(destinationFolder=self.downloadDirectory,
                                         path="MOLT", product="MOD09GA.005",
                                         tiles="h16v01", today=self.endDate,
                                         enddate = self.startDate)
        dm.connect()
        print "Connection Attempts: " + str(dm.nconnection)
        
        dm.getAllDays()
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
        
        
        
        
class MainWindowGui(QtGui.QMainWindow):
    
    def __init__(self,outdir="",parent=None):
        """
            Initialize the GUI window, setting up connections and
            creating member variables.
        
        """
        ## UI GEOMETRY AND SETUP##
        super(MainWindowGui,self).__init__(parent)
        uic.loadUi("ui/test_1.ui",self)
        self.show()
        
        ## SIGNAL CONNECTIONS ##
        #menu actions
        ##File
        self.actionQuit.triggered.connect(self.slotQuitProgram)
        self.actionSaveState.triggered.connect(self.slotSave)
        self.actionSaveStateAs.triggered.connect(self.slotSaveAs)
        self.actionNewProject.triggered.connect(self.slotNewProject)
        self.actionOpenProject.triggered.connect(self.slotOpenProject)
        ##Project 
        self.actionCheckProjectIntegrity.triggered.connect(self.slotCheckProjectIntegrity)
        ##Data
        self.actionDownloadMODIS.triggered.connect(self.slotDownloadMODIS)
        ##Help
        self.actionHelp.triggered.connect(self.slotHelp)
        self.actionAbout.triggered.connect(self.slotAbout)
        
        #button clicks
        self.autoClassifyButton.clicked.connect(self.slotAutoClassify)
        self.manualClassifyButton.clicked.connect(self.slotManualClassify)
        self.lastClassifyButton.clicked.connect(self.slotLastClassify)
        self.undoButton.clicked.connect(self.slotUndo)
        self.redoButton.clicked.connect(self.slotRedo)
        self.acceptButton.clicked.connect(self.slotAccept)
        self.clearButton.clicked.connect(self.slotClear)
        self.saveAltButton.clicked.connect(self.slotSaveAlt)
        
        #confidence selection
        self.cRadio0.toggled.connect(self.slotConfidenceToggled)
        self.cRadio1.toggled.connect(self.slotConfidenceToggled)
        self.cRadio2.toggled.connect(self.slotConfidenceToggled)
        self.cRadio3.toggled.connect(self.slotConfidenceToggled)
        self.cRadio4.toggled.connect(self.slotConfidenceToggled)
        self.cRadio5.toggled.connect(self.slotConfidenceToggled)
        
        #graphics options
        self.overlayCheck.stateChanged.connect(self.slotOverlayOnOff)
        self.overlaySlider.valueChanged.connect(self.slotOverlayTransparency)
        
        
        ## PUBLIC MEMBER VARIABLES ##
        self.projectSaveFileName = None #save file for the project
        self.projectName = None #name of the project
        self.outputDirectory = None #directory to save output
        self.imageInputDirectory = None #directory where the imagery is located
        self.fileQueue = None #queue of files to process
        self.fileQueueIndex = None #index of current file within the queue
        self.imageName = None #filename of the image being classified       
        self.imageXDimension = None #size (pixels) of image in X-direction
        self.imageYDimension = None #size (pixels) of image in Y-direction
        self.imageResolution = None #edge-length of pixels in real world
        self.classification = None #array of classification
        self.classificationSource = None #array of how classification determined
       
        
        ## STARTUP ##
        self.defaultSettings()
    
    
    ### SLOT DEFINITIONS -- MENUS ###
    
    def slotQuitProgram(self):
        print ("Quitting program")
        QtGui.qApp.quit()
    
    def slotSave(self):
        if self.projectSaveFileName:
            self.saveProject(self.projectSaveFileName)
        else:
            self.slotSaveAs()
        print ("Saving state of program")
    
    def slotSaveAs(self):
        fname = QtGui.QFileDialog.getSaveFileName(parent=None,
                      caption="Save Project As")
        self.saveProject(fname)
        print ("Saving state as ...")
    
    def slotNewProject(self):
        #save file dialog
        self.openNewProject()
        #new project dialog
      #  self.newProjectDialog()
        ##name, directory, download data/existing data, shapefile/spatial subset
        print ("Starting new project dialog")
    
    def slotOpenProject(self):
        fname = QtGui.QFileDialog.getOpenFileName(parent=None,
                      caption="Open Existing Project",
                      filter="term-peeper project file (*.tpp);;Any file (*)")
        print (str(fname))
        self.openProject(str(fname))
        print ("Choose the project to open")
    
    def slotHelp(self):
        #help dialog/display
        print ("Help on how to use the program")
    
    def slotAbout(self):
        #about dialog and license information
        try:
            with open("LICENSE.md", 'r') as fin:
                print fin.read()
        except:
            print ("Could not open LICENSE, go to http://www.gnu.org/licenses/gpl-3.0.txt")
    
    
    def slotCheckProjectIntegrity(self):
        print ("Checking Project Integrity")
        
    
    def slotDownloadMODIS(self):
        print ("Downloading MODIS Data")
        self._DMD = DownloadMODISDialog()
        
        
        
    ### SLOT DEFINITIONS -- BUTTONS ###
    
    def slotAutoClassify(self):
        print ("running auto classify")

    def slotManualClassify(self):
        print ("running manual classify")
        
    def slotLastClassify(self):
        print ("running last classify")
        
    def slotUndo(self):
        print ("undoing last action")
        
    def slotRedo(self):
        print ("redoing last action")
        
    def slotAccept(self):
        #store values from GUI
        self.updateUiValues()
        #save all settings to file
        self.outputSingleImage()
        #clear settings to default
        self.defaultSettings()
        #load next image
        if self.fileQueueIndex:
            self.fileQueueIndex = self.fileQueueIndex+1
            if self.fileQueueIndex < len(self.fileQueue):
                self.loadImage()
                print ("accepting and moving to next image")
            else:
                self.outputProject()
                print ("Finished the file queue -- project complete!")
    
    def slotClear(self):
        #question decision to clear
        #reset settings
        self.defaultSettings()
        print ("clearing changes to classification")
    
    def slotSaveAlt(self):
        #write
        print ("saving as alternate")
    
    
    ### SLOT DEFINITIONS -- CONFIDENCE ###
    
    def slotConfidenceToggled(self):
        if self.cRadio0.isChecked():
            self.confidence = 0
        if self.cRadio1.isChecked():
            self.confidence = 1
        if self.cRadio2.isChecked():
            self.confidence = 2
        if self.cRadio3.isChecked():
            self.confidence = 3   
        if self.cRadio4.isChecked():
            self.confidence = 4
        if self.cRadio5.isChecked():
            self.confidence = 5
        print ("Confidence " + str(self.confidence))
    
    
    ### SLOT DEFINITIONS -- GRAPHIC DISPLAY ###
    
    def slotOverlayOnOff(self):
        print ("Class overlay is " + str(self.overlayCheck.isChecked()))
    
    def slotOverlayTransparency(self):
        if self.overlayCheck.isChecked():
          print ("Transparency adjusted to " + str(self.overlaySlider.value()))
          
    
    ### PROJECT IO DIALOGS ###

    def openNewProjectWizard(self,filename=None):
        return 
    
    ### PROJECT IO FUNCTIONS ###
    
    def openProject(self,filename):
        try:
            fin = open(filename,'r')
        except:
            raise IOError("Could not open file " + filename)
        try:
            saveDict = pickle.load(fin)
        except:
            raise BaseException("Could not load the project file, check for file corruption")
        try:
            self.projectName = saveDict['projectname']
            self.fileQueue = saveDict['filequeue']
            self.fileQueueIndex = saveDict['filequeueindex']
            self.outputDirectory = saveDict['outputdirectory']
            self.imageXDimension = saveDict['xdimension']
            self.imageYDimension = saveDict['ydimension']
            self.imageResolution = saveDict['imageresolution']
            self.projectSaveFileName = filename
        except:
            raise BaseException("Could not load all settings from project file, check project integrity")
        
    def saveProject(self,filename):
        if filename != self.projectSaveFileName:
            try:
                fout = open(filename,'w')
            except:
                raise IOError("Could not open file " + filename + " for saving")
        else:
            try:
                fin = open(filename,'r')
                foutOld = open(filename+'.old','w')
                foutOld.write(fin.read())
                fin.close()
                foutOld.flush()
                foutOld.close()
                fout = open(filename,'w')
            except:
                raise IOError("Could not prepare to save over file " + filename)
 
        saveDict = {}
        saveDict['projectname'] = self.projectName
        saveDict['filequeue'] = self.fileQueue
        saveDict['filequeueindex'] = self.fileQueueIndex
        saveDict['outputdirectory'] = self.outputDirectory
        saveDict['xdimension'] = self.imageXDimension
        saveDict['ydimension'] = self.imageYDimension
        saveDict['imageresolution'] = self.imageResolution
        
        try:
            pickle.dump(saveDict,fout)
            print "dumped"
            fout.flush()
            print "flushed"
            fout.close()
            print "closed"
            os.remove(filename+'.old')
            print "old removed"
        except:
            raise IOError("Could not write to file " + filename)

    
    def openNewProject(self):
        fname = QtGui.QFileDialog.getOpenFileName(parent=None,
                      caption="Select New Project File",
                      filter="term-peeper project file (*.tpp)")
        print (str(fname))
        self.saveProject(str(fname))
        self.projectSaveFileName = str(fname)
        self.openNewProjectWizard(filename=str(fname))
    
    
    ### OUTPUT FUNCTIONS ###        
    
    def outputSingleImage(self):
        #prepare text output file
        #prepare image output file
        #write to text
        #write image
        print ("outputting single image")
    
    def outputProject(self):
        print ("outputting project")
    
    
    ### UI FUNCTIONS ###
    
    def defaultSettings(self):
        self.classification = None
        self.classificationSource = None
        self.cRadio0.click()
        self.overlayCheck.setChecked(False)
        self.noteEditor.clear()
        self.overlaySlider.setValue(50)
    
    def updateUiValues(self):
        self.notes = str(self.noteEditor.document().toPlainText())
        if self.cRadio1.isChecked():
            self.confidence = 1
        elif self.cRadio2.isChecked():
            self.confidence = 2
        elif self.cRadio3.isChecked():
            self.confidence = 3   
        elif self.cRadio4.isChecked():
            self.confidence = 4
        elif self.cRadio5.isChecked():
            self.confidence = 5
        else:
            self.confidence = 0
    
    def loadImage(self):
        #change imagery pixmap
        print ("loading image")
        

#### GLOBAL FUNCTION DEFINITIONS ####    

def main():
    app = QtGui.QApplication(sys.argv)
    window = MainWindowGui()
    sys.exit(app.exec_())
          
    
#### SCRIPT ####

if __name__ == '__main__':
    main()
    