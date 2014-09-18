Development Roadmap
===================

This document outlines the planned development of this project.
The design of the project is generally described, and then the development cycle and plans for numbered releases are given.


Design
======

* Python as base language for interactions between modules.
* GUI using Qt4, probably using PyQt as bindings
* PyModis for handling MODIS acquisition, basic processing and clipping
* Pillow for processing and conversion of images, some outputting of results
* scikit-learn for classification of images

Sub-tasks
==========

Data Acquisition
----------------

* Use PyModis to retrieve HDF from NASA's servers
* Have option to store all of these files and conversions locally


Image Processing
----------------

* Use PyModis and MRT to transform HDF into tiffs, project as necessary
* Subset/superset bands and get all relevant bands into 250m resolution
* Use published algorithms to make corrections for sun, clouds, shadows, etc
* Generate masks for clouds and other things to help display


Image Classification
--------------------

* Classify pixels of multispectral images using to-be-determined algorithms (more research needed)
* Allow user to manually apply classification xor overide classification for individual pixels
* Allow user to set 'interests' (e.g. differentiate sediment-laden water from non-)


Interaction
-----------

* GUI for display of imagery and classification map, selection of tools and qualitative certainty, note-taking field
* Load and work on entire folders, subdirectories, list of files.....
* Back and forward progression in image queue
* Undo and Redo manual classification changes
* 'Save state' to permit partial completion of larger task-lists


Output
------

* Raw classifications as well as derivatives for single files (spatial percent class A, percent B...)
* Notes taken for each image

Data Analysis
-------------

* Change detection between files (pixel [i,j] changed from A to B between images n and n+1)
* Time-series analysis (pixel [i,j] is class A 100% of time; pixel [i+1,j] is A from t to t+k, B from t+k to t+m)
* Plot


Numbered Versions
=================

0.1
---

* Download, process, clip, resample, project MODIS data
* View, and manually classify imagery within a GUI
* Load multiple files into a classification queue
* Output raw classification results to files
* Create new projects, open existing, save (as) current


0.2
---

* Automatic classification scheme in place
* Color choices on classification
* Project integrity checks, dynamic projects

0.3
---

* Work flow developments
* Change analysis
