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

import sys
import os
import pickle

from PyQt4 import QtCore, QtGui, uic
#import numpy as np

import modis
import termpeeperIO

###############################################################################

class PickerWidget(QtGui.QGraphicsView):
    """Widget for viewing and making picks"""
    
    def __init__(self,parent=None):
        """Initialize object, create member variables
        
        Parameters
        ----------
        
        parent : QtGui.QGraphicsView
            a parent to inherit from
        
        """
        super(PickerWidget,self).__init__(parent)
        
        # PUBLIC MEMBER VARIABLES #
        self.imagePixmap = None
        self.classPixmap = None
        self.classTransparency = None
        self.classColors = None
        self.origin = None
        
        self.scene = QtGui.QGraphicsScene()
        self.setScene(self.scene)
        
        
        self.updateImage()
        self.show()
    
    def updateImage(self,filename=None):
        #remove old image
        del(self.imagePixmap)
        #make new pixmap
        if not filename:
            self.imagePixmap = QtGui.QPixmap("debug/test_image_KS.tif")
        else:
            self.imagePixmap = QtGui.QPixmap(filename)
        #add new pixmap
        self.scene.addPixmap(self.imagePixmap)
        #scale as necessary
        #?????
        
    def updateClassification(self,class_array):
        """Updates the representation of the classification"""
        pass


###############################################################################             
class MainWindowGui(QtGui.QMainWindow):
    
    def __init__(self,parent=None):
        """Initialize GUI window, set up connections, make member variables
        
        Parameters
        ----------
        
        parent : QtGui.QMainWindow
            A parent to inherit from
        
        
        Post
        ----
        
        Main window is loaded from ui file and drawn on screen.
        Signals and slots are connected.
        Public member variables are created, and self.defaultSettings() is ran.  
        
        """
        
        ## UI GEOMETRY AND SETUP##
        super(MainWindowGui,self).__init__(parent)
        uic.loadUi("ui/main_window.ui",self)
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
        """Cleans up when the program is quit"""
        print ("Quitting program")
        QtGui.qApp.quit()
    
    def slotSave(self):
        """Save the project, using a dialog if project file does not exist"""
        print ("Saving program")
        if self.projectSaveFileName:
            self.saveProject(self.projectSaveFileName)
        else:
            self.slotSaveAs()
        
    
    def slotSaveAs(self):
        """Save the project as a new, or existing, file"""
        print ("Saving state as ...")
        fname = str( QtGui.QFileDialog.getSaveFileName(parent=None,
                      caption="Save Project As"))
        print fname
        self.projectSaveFileName = fname
        self.saveProject(fname)
        
    
    def slotNewProject(self):
        """Create a new project, running the new project dialog"""
        print ("Starting new project dialog")
        #save file dialog
        termpeeperIO.openNewProject()
        
    
    def slotOpenProject(self):
        """Open and existing project
        
        Post
        ----
    
        Parameters from a file are loaded into the variables of the
        current class.
        
        """
        print ("Choose the project to open")
        fname = str( QtGui.QFileDialog.getOpenFileName(parent=None,
                      caption="Open Existing Project",
                      filter="term-peeper project file (*.tpp);;Any file (*)"))
        print (fname)
        saveDict = termpeeperIO.unpackProject(fname)

        try:
            self.projectName = saveDict['projectname']
            self.fileQueue = saveDict['filequeue']
            self.fileQueueIndex = saveDict['filequeueindex']
            self.outputDirectory = saveDict['outputdirectory']
            self.imageXDimension = saveDict['xdimension']
            self.imageYDimension = saveDict['ydimension']
            self.imageResolution = saveDict['imageresolution']
            self.projectSaveFileName = fname
        except:
            raise BaseException("Could not load all settings from project file, check project integrity")
    
    def slotHelp(self):
        """Display help for the program"""
        #help dialog/display
        print ("Help on how to use the program")
    
    def slotAbout(self):
        """Display information about the program, including license"""
        #about dialog and license information
        try:
            with open("LICENSE.md", 'r') as fin:
                print fin.read()
        except:
            print ("Could not open LICENSE, go to http://www.gnu.org/licenses/gpl-3.0.txt")
    
    
    def slotCheckProjectIntegrity(self):
        """Run a test that checks if project is valid"""
        print ("Checking Project Integrity")
        
    
    def slotDownloadMODIS(self):
        """Open a dialof for downloading MIDIS data"""
        print ("Downloading MODIS Data")
        self._DMD = modis.DownloadMODISDialog()
        
        
        
    ### SLOT DEFINITIONS -- BUTTONS ###
    
    def slotAutoClassify(self):
        """Runs the auto classify function on the currently loaded image"""
        print ("running auto classify")

    def slotManualClassify(self):
        """Run a manual classification interface on the current image"""
        print ("running manual classify")
        
    def slotLastClassify(self):
        """Set the classification to that of the previously accepted image"""
        print ("running last classify")
        
    def slotUndo(self):
        """Sometimes life gives you second chances"""
        print ("undoing last action")
        
    def slotRedo(self):
        """Relive your greatest mistakes"""
        print ("redoing last action")
        
    def slotAccept(self):
        """Grab classification, generate output, move to next image
        
        Post
        ----
        
        All stored settings regarding classification are recorded to a file.
        The image queue is advanced.
        The next image is loaded and the GUI is reset to its default state.
        
        """
        print ("accepting and moving to next image")
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
                self.imageView.updateImage(self.fileQueue[self.fileQueueIndex])
                
            else:
                self.outputProject()
                print ("Finished the file queue -- project complete!")
    
    def slotClear(self):
        """Resets the GUI to its default state"""
        #question decision to clear
        #reset settings
        print ("clearing changes to classification")
        self.defaultSettings()
       
    
    def slotSaveAlt(self):
        """Saves the classification to an alternate output file"""
        #write
        print ("saving as alternate")
    
    
    ### SLOT DEFINITIONS -- CONFIDENCE ###
    
    def slotConfidenceToggled(self):
        """Sets confidence to user's choice"""
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
        """Modifies whether the classification overlay is drawn"""
        print ("Class overlay is " + str(self.overlayCheck.isChecked()))
    
    def slotOverlayTransparency(self):
        """Changes the transparency of the classification overlay"""
        if self.overlayCheck.isChecked():
          print ("Transparency adjusted to " + str(self.overlaySlider.value()))
          
    ### IO FUNCTIONS ###
    
    def saveProject(self,filename):
        """Retrieves the current project state and saves it to file
        
        Parameters
        ----------
        
        filename : str
            the file to save to
            
        
        Post
        ----
        
        The project file has been saved, or errors raised indicate it has not
        
        """
        saveDict = {}
        saveDict['projectsavename'] = self.projectSaveFileName
        saveDict['projectname'] = self.projectName
        saveDict['filequeue'] = self.fileQueue
        saveDict['filequeueindex'] = self.fileQueueIndex
        saveDict['outputdirectory'] = self.outputDirectory
        saveDict['xdimension'] = self.imageXDimension
        saveDict['ydimension'] = self.imageYDimension
        saveDict['imageresolution'] = self.imageResolution
        termpeeperIO.packProject(filename,saveDict)
       
        
    ### UI FUNCTIONS ###
    
    def defaultSettings(self):
        """Sets the default settings for the GUI"""
        self.classification = None
        self.classificationSource = None
        self.cRadio0.click()
        self.overlayCheck.setChecked(False)
        self.noteEditor.clear()
        self.overlaySlider.setValue(50)
    
    def updateUiValues(self):
        """Stores current GUI settings to the classes variables"""
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
    
    def loadImage(self,filename):
        """Draws an image to the screen"""
        #change imagery pixmap
        self.imageView.updateImage(filename)
        print ("loading image")
        

#### GLOBAL FUNCTION DEFINITIONS ####    

def main():
    """Main execution function, draws main window"""
    app = QtGui.QApplication(sys.argv)
    window = MainWindowGui()
    sys.exit(app.exec_())
          
    
#### SCRIPT ####

if __name__ == '__main__':
    main()
    