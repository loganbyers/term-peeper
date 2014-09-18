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

import pickle
import os

from PyQt4 import QtGui

###############################################################################

### PROJECT WINDOWS ###

class NewProjectWizard(QtGui.QWizard):
    pass 

class ProjectIntegrityDialog(QtGui.QDialog):
    pass
  



### PROJECT IO FUNCTIONS ###

def openNewProject():
    """Opens a new project using a wizard, and saves this file"""
    fname = str( QtGui.QFileDialog.getSaveFileName(parent=None,
                  caption="Select New Project File",
                  filter="term-peeper project file (*.tpp)"))
    print fname
    packProject(fname,openNewProjectWizard(filename=fname))

def openNewProjectWizard(filename=None):
    """Opens the new project wizard"""
    return #dict

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
    
    
    Note
    ----
    
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
    