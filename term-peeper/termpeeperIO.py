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
#  Modified: 2014.09.25
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

import pickle
import os

from PyQt4 import QtGui, uic

import modis
from pymodis import convertmodis_gdal as convertmodis

###############################################################################

### PROJECT WINDOWS ###

class NewProjectWizard(QtGui.QWizard):
    """Wizard for creating new project file"""
    def __init__(self,parent=None,filename=None):
        """Initialization function

        Parameters
        ----------

        parent : QtGui.QWizard
            parent to inherit

        filename : str
            default save file

        """

        super(NewProjectWizard,self).__init__(parent)

        self.finished.connect(self.makeProject)

        self.intro = self.addPage(self.IntroPage(self,filename))
        self.img = self.addPage(self.ImagePage(self))

        self.setFixedSize(660,520)
        self.show()

    def convertBandNumbersToSubsetList(self,bands):
        bands = map(int,bands.split(','))
        return [1 if k in bands else 0 for k in range(1,max(bands)+1)]


    def makeProject(self):
        """Take values from wizard pages and make project file

        Post
        ----

        save file is created with information from the wizard

        """
        print "making project now"
        self.introPage = self.page(self.intro)
        print self.introPage.saveLineEdit.text()
        self.imgPage = self.page(self.img)

        saveDict = {}
        saveDict['projectsavename'] = self.introPage.saveLineEdit.text()
        saveDict['projectname'] = self.introPage.projectNameLineEdit.text()
        saveDict['author'] = self.introPage.authorLineEdit.text()
        saveDict['glacier'] = self.introPage.glacierLineEdit.text()
        saveDict['outputprefix'] = self.introPage.prefixLineEdit.text()
        saveDict['outputdirectory'] = self.introPage.outputDirLineEdit.text()
        saveDict['description'] = self.introPage.descriptionPlainTextEdit.toPlainText()
        saveDict['clipfile'] = self.imgPage.clipLineEdit.text()
        saveDict['hdfbands'] = self.imgPage.hdfBandsLineEdit.text()
        saveDict['epsg'] = self.imgPage.epsgLineEdit.text()
        saveDict['pixelsize'] = self.imgPage.pixelSizeLineEdit.text()

        saveDict = {key : str(saveDict[key]) for key in saveDict.keys()}
        hdfQueue = []
        for i in range(self.imgPage.fileListWidget.count()):
            hdfQueue.append(str(self.imgPage.fileListWidget.item(i).text()))
            #print fileQueue[-1]


        packProject(saveDict['projectsavename'],saveDict)

        pathToFullImages = os.path.join(saveDict['outputdirectory'],'TEMP_GTIFF')
        pathToFullImages = pathToFullImages + os.sep
        if not os.path.exists(saveDict['outputdirectory']) and saveDict['outputdirectory']:
            os.mkdir(saveDict['outputdirectory'])
        if not os.path.exists(pathToFullImages):
            os.mkdir(pathToFullImages)
        bandsInOrder = map(int,saveDict['hdfbands'].split(','))
        sortedBands = sorted(bandsInOrder)
        bandRank = [sortedBands.index(v) for v in bandsInOrder]

        llx, lly, urx, ury = modis.getShapefileBoundingBox(saveDict['clipfile'])
        fileQueue = []

        for f in hdfQueue:
            hdfName = '.'.join( (os.path.split(f)[-1]).split('.')[:-1])

            con = convertmodis.convertModisGDAL(f,pathToFullImages,
                               self.convertBandNumbersToSubsetList(saveDict['hdfbands']),
                               int(saveDict['pixelsize']),'GTiff',epsg=int(saveDict['epsg']))
            con.run()

            imagesInOrder = []
            images = sorted(os.listdir(pathToFullImages))
            for i in range(len(images)):
                imagesInOrder.append(os.path.join(pathToFullImages,images[bandRank.index(i)]))
            print imagesInOrder
            RGBRaster = os.path.join(pathToFullImages,'RGB.tif')
            RGBRaster8Bit = os.path.join(pathToFullImages,saveDict['outputprefix']+hdfName+'.tif')
            clippedRaster = os.path.join(saveDict['outputdirectory'],saveDict['outputprefix']+hdfName+'.tif')

            modis.compositeRasterBandsToRGB(imagesInOrder,RGBRaster,llx,lly,urx,ury)
            modis.convertRasterTo8Bit(RGBRaster,RGBRaster8Bit)
            modis.clipRasterWithShape(RGBRaster8Bit,clippedRaster,saveDict['clipfile'])
            fileQueue.append(clippedRaster)

            for rm in os.listdir(pathToFullImages):
                os.remove(os.path.join(pathToFullImages,rm))

            print hdfName

        os.rmdir(pathToFullImages)


        saveDict['filequeue'] = tuple(fileQueue)
        saveDict['filequeueindex'] = 0

        # image and tiff-based attributes
        saveDict['imageresolution'] = None
        saveDict['xdimension'] = None
        saveDict['ydimension'] = None


        packProject(saveDict['projectsavename'],saveDict)
        pass

    ### WIZARD PAGE CLASSES ###

    class IntroPage(QtGui.QWizardPage):
        """Introductory project setup wizard page"""
        def __init__(self,parent=None,filename=None):
            """Initialization of class

            Parameters
            ----------

            parent : QtGui.QWizard
                the parent the page should belong to

            filename : str
                the default file for saving the project

            """

            super(parent.IntroPage,self).__init__(parent)
            uic.loadUi('ui/new_project_wizard_page_0.ui',self)

            self.saveFileOpenButton.clicked.connect(self.slotFileOpen)
            self.outputDirOpenButton.clicked.connect(self.slotDirOpen)

            if filename:
                self.saveLineEdit.setText(filename)
            self.prefixLineEdit.setText('test')


        def slotFileOpen(self):
            """Open a new file dialog"""
            fname = str( QtGui.QFileDialog.getSaveFileName(parent=None,
                      caption="Open New Project",
                      filter="term-peeper project file (*.tpp);;Any file (*)"))
            self.saveLineEdit.setText(fname)
            pass


        def slotDirOpen(self):
            """Open an existing directory dialog"""
            dname = str( QtGui.QFileDialog.getExistingDirectory())
            self.outputDirLineEdit.setText(dname)
            pass



    class ImagePage(QtGui.QWizardPage):
        """Wizard page for defining imagery to process"""
        def __init__(self,parent=None):
            """Initialization of class

            Parameters
            ----------

            parent : QtGui.QWizard
                the parent this page should belong to

            """
            super(parent.ImagePage,self).__init__(parent)
            uic.loadUi('ui/new_project_wizard_page_1.ui',self)

            self.fileListWidget.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
            self.fileListWidget.setDragEnabled(True)
            self.fileListWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.removeListButton.clicked.connect(self.slotRemoveFromList)
            self.sortButton.clicked.connect(self.slotSortList)

            self.clipOpenFileButton.clicked.connect(self.slotClipOpenFile)
            self.txtOpenFileButton.clicked.connect(self.slotTxtOpenFile)
            self.txtFileToListButton.clicked.connect(self.slotTxtAddFiles)
            self.importFileButton.clicked.connect(self.slotImportFiles)
            self.downloadDataButton.clicked.connect(self.slotDownloadData)

        def sortModisFilesByDate(self,fileList):
            def sortKey(filename):
                return filename.split('.')[1]
            sortedByDate = sorted(fileList,key=sortKey)
            for i in range(len(fileList)-1):
                first = os.path.split(sortedByDate[i])[-1]
                second = os.path.split(sortedByDate[i+1])[-1]
                if sortKey(first) == sortKey(second):
                    if first.split('.')[0] > second.split('.')[0]:
                        swap = sortedByDate[i]
                        sortedByDate[i] = sortedByDate[i+1]
                        sortedByDate[i+1] = swap
            return sortedByDate

        def slotClipOpenFile(self):
            """Open file to clip the imagery to"""
            fname = str( QtGui.QFileDialog.getOpenFileName(parent=None,
                      caption="Open Mask File",
                      filter="shapefile (*.shp);;well-known type (.wkt);;Any file (*)"))
            self.clipLineEdit.setText(fname)
            pass

        def slotTxtOpenFile(self):
            """Open text file that is an imagery queue"""
            fnames = str( QtGui.QFileDialog.getOpenFileName(parent=None,
                      caption="Open File List",
                      filter="Any file (*)"))
            self.txtLineEdit.setText(fnames)
            pass

        def slotTxtAddFiles(self):
            """Add the files specified by the text file to the list"""
            fname = self.txtLineEdit.text()
            if not os.path.isfile(fname):
                print ("No text file selected")
                return

            try:
                fin = open(fname,'r')
            except:
                raise IOError("Could not open image import file\n"
                              "Tried to open file\n"+fname)
            try:
                self.fileListWidget.addItems(fin.read().splitlines())
            except:
                print ("Could not add items during import")
            try:
                fin.close()
            except:
                raise IOError("Could not close image import file\n"
                              "Tried to close file\n"+fname)

        def slotImportFiles(self):
            """Add existing MODIS HDF to the queue"""
            fnames = QtGui.QFileDialog.getOpenFileNames(parent=None,
                      caption="Open Files",
                      filter="MODIS HDF (*.hdf);;Any Files (*)")
            fnames_str = map(str,fnames)
            fnames_sort = self.sortModisFilesByDate(fnames_str)
            for f in fnames_sort:
                print f
            self.fileListWidget.addItems(fnames_sort)
            pass

        def slotDownloadData(self):
            """Download MODIS data"""
            self._DMD = modis.DownloadMODISDialog()
            pass


        def slotRemoveFromList(self):
            """Removes selected files from list"""
            selected = self.fileListWidget.selectedItems()
            for item in selected:
                print item
                self.fileListWidget.takeItem(self.fileListWidget.row(item))

        def slotSortList(self):
            sortedList = []
            for i in range(self.fileListWidget.count()):
                sortedList.append(str(self.fileListWidget.item(i).text()))
            self.fileListWidget.clear()
            self.fileListWidget.addItems(self.sortModisFilesByDate(sortedList))
            pass



class ProjectIntegrityDialog(QtGui.QDialog):
    pass




### PROJECT IO FUNCTIONS ###

def unpackProject(filename):
    """Opens an existing project and returns a dictionary describing it

    Parameters
    ----------

    filename : str
        the file to open, ideally would be a .tpp file


    Raises
    ------

    IOError if file can not be opened

    BaseException if file could not be loaded or is corrupted


    Notes
    -----

    File IO for this project uses the pickle module.
    Relevant variables are stored in a dictionary, and then pickled.


    """
    try:
        fin = open(filename,'r')
    except:
        raise IOError("Could not open file " + filename)
    try:
        saveDict = pickle.load(fin)
    except:
        raise BaseException("Could not unpack the project file, check for file corruption")
    fin.close()
    return saveDict



def packProject(filename,saveDict):
    """Saves the current state of a project to a file

    Parameters
    ----------

    filename : str
        the file to save project to

    saveDict : dict
        dictionary describing project state


    Post
    ----

    Save file is written, with parameters taken from `saveDict`.


    Raises
    ------

    IOError if files could not be opened for saving or could not be saved


    Notes
    -----

    To prevent corruption and loss of the save file, a temporary
    file is created with the suffix `.old`.
    If file is saved without apparent errors, then this `.old` file
    is removed and deleted.
    If file saving does cause a problem, this `.old` file can be salvaged.


    """
    if filename == '' or not filename:
        print "Filename not specified -- project not saved"
        return
    if not os.path.exists(filename):
        try:
            fout = open(filename,'w')
        except:
            raise IOError("Could not open file " + filename + " for saving")
    else: #if file already exists
        try:
            #copy existing version, open fout
            fin = open(filename,'r')
            foutOld = open(filename+'.old','w')
            foutOld.write(fin.read())
            fin.close()
            foutOld.flush()
            foutOld.close()
            fout = open(filename,'w')
        except:
            raise IOError("Could not prepare to save over file " + filename)
    try:
        pickle.dump(saveDict,fout)
        fout.flush()
        fout.close()
        if os.path.exists(filename+'.old'):
            os.remove(filename+'.old')
        print ("Project File Saved")
    except:
        raise IOError("Could not write to file " + filename)


### CLASSIFICATION OUTPUT FUNCTIONS ###

def outputSingleImage():
    """Outputs the classification to a file"""
    #prepare text output file
    #prepare image output file
    #write to text
    #write image
    print ("outputting single image")

def outputProject():
    """Outputs the results of an entire project to a file"""
    print ("outputting project")
