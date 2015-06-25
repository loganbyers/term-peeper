#! /usr/bin/env python
#
#  term-peeper is a program for classifying MODIS imagery of glacier termini
#  this file is part of term-peeper
#
#  Copyright 2014-2015 Logan C Byers
#
#  Authors: Logan C Byers
#  Contact: loganbyers@ku.edu
#  Date: 2014.09.18
#  Modified: 2015.06.25
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
import json

from PyQt4 import QtCore, QtGui, uic
import numpy as np
import gdal

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
        
        self.initialize()
        
    def initialize(self,filename=None):
        # PUBLIC MEMBER VARIABLES #
        
        self.imageArray = None
        self.imageFormat = None
        self.satelliteImage = None
        self.imagePixmap = None
        self.classArray = None
        self.classARGB = None
        self.classImage = None
        self.classPixmap = None
        self.classPixmapItem = None
        
        self.origin = None
        self.manualClassificationMode = None
        self.currentClassValue = None
        
        self.noDataValue = 255
        self.noDataColor = [255,255,255,0]
        self.glacierValue = 1
        self.glacierColor = [153,125,51,255]
        self.icebergValue = 5
        self.icebergColor = [100,200,200,255]
        self.waterValue = 25
        self.waterColor = [153,51,255,255]
        
        self.scene = QtGui.QGraphicsScene()
        self.setScene(self.scene)
        
        self.initializeArrays(filename)
        
        #load classification related objects
    def initializeArrays(self,filename=None,bands=None):
        self.loadImageToArray(filename,bands)
        self.updateImageDraw()
        self.defaultClassification()
        self.classToARGB()
        self.classPixmap = QtGui.QPixmap()
        self.classPixmapItem = self.scene.addPixmap(self.classPixmap)
        self.updateClassDraw()
        self.show()
        
    ### SATELLITE IMAGES ###
    def updateImageDraw(self):
        #remove old image
        del(self.imagePixmap)
        arrayShape = self.imageArray.shape
        self.satelliteImage = QtGui.QImage(self.imageArray.data, 
                                           arrayShape[1], arrayShape[0], 
                                           self.imageArray.strides[0], self.imageFormat)
        self.imagePixmap = QtGui.QPixmap.fromImage(self.satelliteImage)
        self.imagePixmap = self.imagePixmap.scaled(400,400,QtCore.Qt.KeepAspectRatio)
        self.scene.addPixmap(self.imagePixmap)
      
      
    def loadImageToArray(self,filename=None,bands=None):    
        if not filename:
            filename = "debug/test_image_KS.tif"
        dataset = gdal.Open(filename, gdal.GA_ReadOnly)
        if not bands:
            bandCount = dataset.RasterCount
        else:
            bandCount = len(bands)
        if bandCount == 1:
            self.imageFormat = QtGui.QImage.Format_Indexed8
        if bandCount == 3:
            self.imageFormat = QtGui.QImage.Format_RGB888
        arrayShape = (dataset.RasterYSize,dataset.RasterXSize,bandCount)
        self.imageArray = np.empty(arrayShape,dtype=np.uint8)
        for i in range(bandCount):
            self.imageArray[:,:,i] = dataset.GetRasterBand(i+1).ReadAsArray()
    
    ### CLASSIFICATION FUNCTIONS ###
    
    def defaultClassification(self):
        shape = self.imageArray.shape
        self.classArray = np.empty((shape[0],shape[1]),dtype=np.uint8)
        self.classArray.fill(self.noDataValue)
    
    def classToARGB(self):
        shape = self.classArray.shape
        self.classARGB = np.empty((shape[0],shape[1],4),dtype=np.uint8)
        self.classARGB[self.classArray == self.glacierValue] = self.glacierColor
        self.classARGB[self.classArray == self.icebergValue] = self.icebergColor
        self.classARGB[self.classArray == self.waterValue] = self.waterColor
        self.classARGB[self.classArray == self.noDataValue] = self.noDataColor
    
    def updateClassDraw(self):
        """Updates the representation of the classification"""
        self.classImage = QtGui.QImage(self.classARGB.data, 
                                           self.classARGB.shape[1], self.classARGB.shape[0], 
                                           self.classARGB.strides[0], QtGui.QImage.Format_ARGB32)
        self.classPixmap = QtGui.QPixmap.fromImage(self.classImage)
        self.classPixmap = self.classPixmap.scaled(400,400,QtCore.Qt.KeepAspectRatio)
        self.classPixmapItem.setPixmap(self.classPixmap)
        
    
    def setAlpha(self,alpha):
        if alpha > 255:
            alpha = np.uint8(255)
        elif alpha < 0:
            alpha = np.uint8(0)
        else:
            alpha = np.uint8(alpha)
        self.glacierColor[3] = alpha
        self.icebergColor[3] = alpha
        self.waterColor[3] = alpha
        self.classToARGB()
        
        
    ### USER INTERACTION ###
    
    def mousePositionToArray(self,qpoint):
        rows, cols = self.classArray.shape
        rowmajor = rows/400.0
        colmajor = cols/400.0
        if rowmajor > colmajor:
            scale = rowmajor
        else:
            scale = colmajor
        row = scale * qpoint.y()
        col = scale * qpoint.x()
        print row, col
        return int(row), int(col)
      
    def isNoDataLocation(self,pos):
        return (self.imageArray[pos[1],pos[0],:3] == [255,255,255]).all()
      
    def mousePressEvent(self,mouse):
        if not self.manualClassificationMode:
            return
        mousePosition = self.mapToScene(mouse.pos())  
        iy,ix = self.mousePositionToArray(mousePosition)
        if mouse.button() == QtCore.Qt.LeftButton:
            if not self.isNoDataLocation((ix,iy)): 
                self.classArray[iy,ix] = self.currentClassValue
        elif mouse.button() == QtCore.Qt.MiddleButton:
            print "middle"
        elif mouse.button() == QtCore.Qt.RightButton:
            if not self.isNoDataLocation((ix,iy)):
                self.floodFillClassification(self.classArray[iy,ix],self.currentClassValue,(ix,iy))
                print "right"
        self.classToARGB()
        self.updateClassDraw()
        print mousePosition
        
        
    def floodFillClassification(self,target,replace,pos):
        if self.classArray[pos[1],pos[0]] == replace:
            return
        if self.classArray[pos[1],pos[0]] != target:
            return
        q = [pos]
        while q:
            x,y = q[0]
            q = q[1:]
            if self.classArray[y,x] == target and not self.isNoDataLocation((x,y)):
                self.classArray[y,x] = replace
                if x != 0:
                    q.append((x-1,y))
                if x != self.classArray.shape[1] - 1:
                    q.append((x+1,y))
                if y != 0:
                    q.append((x,y-1))
                if y != self.classArray.shape[0] - 1:
                    q.append((x,y+1))
                
        
        

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
        
        #classification options
        self.overlayCheck.stateChanged.connect(self.slotOverlayOnOff)
        self.overlaySlider.valueChanged.connect(self.slotOverlayTransparency)
        self.glacierButton.clicked.connect(self.slotClassColorSelect)
        self.icebergButton.clicked.connect(self.slotClassColorSelect)
        self.waterButton.clicked.connect(self.slotClassColorSelect)
        self.noDataButton.clicked.connect(self.slotClassColorSelect)
        
        ## PUBLIC MEMBER VARIABLES ##
        self.projectSaveFileName = None #save file for the project
        self.projectName = None #name of the project
        self.outputDirectory = None #directory to save output
        self.outputPrefix = None #prefix string for the output
        self.imageInputDirectory = None #directory where the imagery is located
        self.fileQueue = None #queue of files to process
        self.fileQueueIndex = None #index of current file within the queue 
        self.imageXDimension = None #size (pixels) of image in X-direction
        self.imageYDimension = None #size (pixels) of image in Y-direction
        self.imageResolution = None #edge-length of pixels in real world
        self.clipFile = None #clip file for masking the data
        self.author = None #author of the project
        self.glacier = None #glacier being studied
        self.projectDescription = None #long description of the project
        
        
        self.imageName = None #filename of the image being classified  
        self.classification = None #array of classification
        self.classificationARGB = None
        self.classificationSource = None #array of how classification determined
        self.classificationList = []
        
        ## PUBLIC RUNTIME OBJECTS ##
        self.currentClassChoice = None
        
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
        fileDialog = QtGui.QFileDialog.getSaveFileName(parent=None,
                          caption="Create New Project",
                          filter="term-peeper project file (*.tpp);;Any file (*)")
        fname = str(fileDialog)
        #fname = str( QtGui.QFileDialog.getSaveFileName(parent=None,
                          #caption="Create New Project",
                          #filter="term-peeper project file (*.tpp);;Any file (*)"))
        print 'dialog opened'
        #termpeeperIO.openNewProject()
        self._NPW = termpeeperIO.NewProjectWizard(filename=fname)
    
    def slotOpenProject(self,filename=None):
        """Open an existing project
        
        Post
        ----
    
        Parameters from a file are loaded into the variables of the
        current class.
        
        """
        if not filename:
            print ("Choose the project to open")
            filename = str( QtGui.QFileDialog.getOpenFileName(parent=None,
                          caption="Open Existing Project",
                          filter="term-peeper project file (*.tpp);;Any file (*)"))
            print (filename)
        saveDict = termpeeperIO.unpackProject(filename)
        
        try:
            self.projectName = saveDict['projectname']
            self.author = saveDict['author']
            self.glacier = saveDict['glacier']
            self.fileQueue = saveDict['filequeue']
            self.fileQueueIndex = saveDict['filequeueindex']
            self.outputDirectory = saveDict['outputdirectory']
            self.outputPrefix = saveDict['outputprefix']
            self.projectDescription = saveDict['description']
            self.imageXDimension = saveDict['xdimension']
            self.imageYDimension = saveDict['ydimension']
            self.imageResolution = saveDict['pixelsize']
            self.clipFile = saveDict['clipfile']
            self.projectSaveFileName = filename  
        except:
            raise BaseException("Could not load all settings from project file, check project integrity")
        self.loadImage(self.fileQueue[self.fileQueueIndex])
        self.defaultSettings()
        #make a fresh classification
        #self.imageView.initialize()
        #self.slotManualClassify()
        
        
        print saveDict
        
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
        if self.manualClassifyButton.isChecked():
            print ("starting manual classify")
            self.imageView.manualClassificationMode = True
        else:
            print ("stopping manual classify")
            self.imageView.manualClassificationMode = False
        
    def slotLastClassify(self):
        """Set the classification to that of the previously accepted image"""
        if self.fileQueueIndex:
            self.imageView.classArray = self.classificationList[-1].copy()
            self.imageView.classToARGB()
            self.imageView.updateClassDraw()
            self.imageView.show()
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
        self.storeClassification()
        self.outputScene()
        #load next image
        if self.fileQueueIndex >= 0:
            self.fileQueueIndex = self.fileQueueIndex + 1
            if self.fileQueueIndex < len(self.fileQueue):
                self.loadImage(self.fileQueue[self.fileQueueIndex])
                
            else:
                #self.outputProject()
                print ("Finished the file queue -- project complete!")
            print "fileQueueIndex = ", self.fileQueueIndex
        #clear settings to on GUI
        self.defaultSettings()
        #make a fresh classification
        #self.imageView.initialize()
        self.slotManualClassify()
        
    
    def slotClear(self):
        """Resets the GUI to its default state"""
        #question decision to clear
        #reset settings
        print ("clearing changes to classification")
        self.defaultSettings()
        self.imageView.initialize(self.fileQueue[self.fileQueueIndex])
       
    
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
    
    
    ### SLOT DEFINITIONS -- CLASSIFICATION ###
    
    def slotOverlayOnOff(self):
        """Modifies whether the classification overlay is drawn"""
        if self.overlayCheck.isChecked():
            self.imageView.setAlpha(np.uint8(self.overlaySlider.value()*2.55))
            self.imageView.updateClassDraw()
            self.imageView.show()
        else:
          self.imageView.setAlpha(np.uint8(0))
          self.imageView.updateClassDraw()
          self.imageView.show()
        
        print ("Class overlay is " + str(self.overlayCheck.isChecked()))
    
    def slotOverlayTransparency(self):
        """Changes the transparency of the classification overlay"""
        if self.overlayCheck.isChecked():
          self.imageView.setAlpha(np.uint8(self.overlaySlider.value()*2.55))
          self.imageView.updateClassDraw()
          self.imageView.show()
          print ("Opacity adjusted to " + str(self.overlaySlider.value()))
    
    def slotClassColorSelect(self):
        """Changes which ground class is used in manual classification mode"""
        if self.glacierButton.isChecked():
            self.imageView.currentClassValue = self.imageView.glacierValue
        elif self.icebergButton.isChecked():
            self.imageView.currentClassValue = self.imageView.icebergValue 
        elif self.waterButton.isChecked():
            self.imageView.currentClassValue = self.imageView.waterValue  
        elif self.noDataButton.isChecked():
            print "NODATA!!!"
            self.imageView.currentClassValue = self.imageView.noDataValue 
            
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
       
    ### CLASSIFICATION FUNCTIONS ###
    def storeClassification(self):
        """Retrieves the classification image to save results"""
        self.classification = self.imageView.classArray.copy()
        self.classificationARGB = self.imageView.classARGB.copy()
        self.classificationList.append(self.imageView.classArray.copy())
   
    def packSceneInDict(self):
        d = {}
        d['projectname'] = self.projectName
        d['author'] = self.author
        d['glacier'] = self.glacier
        d['satteliteimage'] = self.fileQueue[self.fileQueueIndex]
        d['classification'] = self.classification.tolist()
        d['pixelsize'] = self.imageResolution
        d['notes'] = self.notes
        d['confidence'] = self.confidence
        d['classificationvalues'] = [['glacier',self.imageView.glacierValue],\
                                     ['iceberg',self.imageView.icebergValue],\
                                     ['water',self.imageView.waterValue],\
                                     ['nodata',self.imageView.noDataValue]]
        return d
   
    def outputScene(self):
        outputDir = os.path.join(self.outputDirectory,'output')
        textDir = os.path.join(outputDir,'text')
        imageDir = os.path.join(outputDir,'img')
        if not os.path.exists(outputDir):
            os.mkdir(outputDir)
        if not os.path.exists(textDir):
            os.mkdir(textDir)
        if not os.path.exists(imageDir):
            os.mkdir(imageDir)
         
        if len(self.fileQueue) > 999:
            digits = 4
        elif len(self.fileQueue) > 99:
            digits = 3
        elif len(self.fileQueue) > 9:
            digits = 2
        else:
            digits = 1
        strNum = str(self.fileQueueIndex)
        while len(strNum) < digits:
            strNum = '0'+strNum
        textOutput = os.path.join(textDir,'scene'+strNum+'.txt')
        imageOutput = os.path.join(imageDir,'scene'+strNum+'.tif')
        fout = open(textOutput,'w')
        fout.write(json.dumps(self.packSceneInDict(),indent=4,sort_keys=True))
        fout.close()
        self.createClassificationGeotiff(imageOutput)
        
        print 'SCENE OUTPUT'
    
    def createClassificationGeotiff(self,filename):
        src_ds = gdal.Open(self.fileQueue[self.fileQueueIndex])
        driver = gdal.GetDriverByName('GTiff')
        dst_ds = driver.CreateCopy(filename, src_ds, 0)  
        dst_ds.GetRasterBand(1).WriteArray(self.classificationARGB[:,:,2])
        dst_ds.GetRasterBand(2).WriteArray(self.classificationARGB[:,:,1])
        dst_ds.GetRasterBand(3).WriteArray(self.classificationARGB[:,:,0])
        dst_ds = None
    
    ### UI FUNCTIONS ###
    
    def defaultSettings(self):
        """Sets the default settings for the GUI"""
        self.classification = None
        self.classificationSource = None
        self.cRadio0.click()
        self.noteEditor.clear()
        #self.overlayCheck.setChecked(False)
        #self.overlaySlider.setValue(75)
    
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
        self.imageView.initialize(filename)
        print ("loading image: " + filename)
        

#### GLOBAL FUNCTION DEFINITIONS ####    

def main():
    """Main execution function, draws main window"""
    app = QtGui.QApplication(sys.argv)
    window = MainWindowGui()
    sys.exit(app.exec_())
          
    
#### SCRIPT ####

if __name__ == '__main__':
    main()
    