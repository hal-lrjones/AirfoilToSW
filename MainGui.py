import sys
import os.path
import copy
import numpy
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel, QPushButton, QLineEdit, QDoubleSpinBox, QCheckBox, QRadioButton, QFileDialog
from pyqtgraph import PlotWidget
from PyQt6.QtCore import QSettings

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("MainGui.ui", self)

        #Define Session data variables
        self.settings = QSettings('AirfoilToSW', 'Settings')
        self.foilOpenDirectory = None
        self.foilList = []
        self.foilSaveDirectory = None

        #Apply Last session's settings
        try:
            self.resize(self.settings.value('window size'))
            self.move(self.settings.value('window position'))
        except:
            pass

        #Define Widgets
        self.cordinateLabel = self.findChild(QLabel,"cordinateLabel")
        self.foilPlot1 = self.findChild(PlotWidget, "foilPlot1")
        self.foilPlot2 = self.findChild(PlotWidget, "foilPlot2")
        self.foilPlot3 = self.findChild(PlotWidget, "foilPlot3")
        self.foilPlot1.setTitle("Foil 1")
        self.foilPlot2.setTitle("Foil 2")
        self.foilPlot3.setTitle("Foil 3")
        self.foilPlot1.setAspectLocked()
        self.foilPlot2.setAspectLocked()
        self.foilPlot3.setAspectLocked()
        self.exportButton = self.findChild(QPushButton,"exportButton")
        self.exportDirectory = self.findChild(QPushButton,"exportDirectory")
        self.exportLocalLineEdit = self.findChild(QLineEdit,"exportLocalLineEdit")
        self.importButton = self.findChild(QPushButton, "importButton")
        self.labelSelectedFoils = self.findChild(QLabel, "labelSelectedFoils")
        self.check0XY = self.findChild(QCheckBox,"check0XY")
        self.checkYX0 = self.findChild(QCheckBox,"checkYX0")
        self.check0YX = self.findChild(QCheckBox,"check0YX")
        self.checkX0Y = self.findChild(QCheckBox,"checkX0Y")
        self.checkXY0 = self.findChild(QCheckBox,"checkXY0")
        self.checkY0X = self.findChild(QCheckBox,"checkY0X")
        self.checkMirrorX = self.findChild(QCheckBox,"checkMirrorX")
        self.checkMirrorY = self.findChild(QCheckBox,"checkMirrorY")
        self.doubleSpinAlpha = self.findChild(QDoubleSpinBox,"doubleSpinAlpha")
        self.radioButtonLE = self.findChild(QRadioButton, "radioButtonLE")
        self.radioButtonTE = self.findChild(QRadioButton, "radioButtonTE")
        self.doubleSpinScale = self.findChild(QDoubleSpinBox,"doubleSpinScale")
        self.updatePlotsButton = self.findChild(QPushButton, "updatePlotsButton")

        #Widget Logic
        self.exportButton.clicked.connect(self.export)
        self.exportDirectory.clicked.connect(self.getFileSaveDirectory)
        self.importButton.clicked.connect(self.importFoils)
        self.updatePlotsButton.clicked.connect(self.updatePlots)

    #save Session setings
    def closeEvent(self,event):
        self.settings.setValue('window size', self.size())
        self.settings.setValue('window position', self.pos())
        event.accept()

    def extractCords(self, name, file):
        f = open(file, "r")
        f.readline()

        xCord = []
        yCord = []
        points = []

        for row in f: #loop through each row
            points.append(row.lstrip().rstrip()) #remove any spaces before or after cordinates and add result to points list

        for i in points:
            delim = ' '*i.count(' ')    #count how many spaces are between data points
            holder = i.split(delim)     #split each point into x and y cordinates
            xCord.append(float(holder[0]))
            yCord.append(float(holder[1]))
        f.close()

        activeFoil = foil(name,xCord,yCord)
        self.foilList.append(activeFoil)
        self.updatePlots()

    def importFoils(self):
        fOpenName = QFileDialog.getOpenFileNames(self,"Open File",self.foilOpenDirectory,"Dat Files (*.dat);;Text Files (*.txt)")
        if 0 < len(fOpenName[0]) and os.path.isfile(fOpenName[0][0]):
            self.foilOpenDirectory = os.path.dirname(fOpenName[0][0])
            nameLabel = "Selected Foils:"
            self.foilList.clear()
            for file in fOpenName[0]:
                name = os.path.basename(file)
                nameLabel = f"{nameLabel} {name},"
                self.extractCords(name, file)
            self.labelSelectedFoils.setText(nameLabel)
    
    def getFileSaveDirectory(self):
        self.foilSaveDirectory = QFileDialog.getExistingDirectory(self,"Select Save Location",self.foilOpenDirectory)
        self.exportLocalLineEdit.setText(self.foilSaveDirectory)

    def export(self):
        if self.foilSaveDirectory is not None:
            holderFoilList = self.applyFoilExportSettings()
            for activeFoil in holderFoilList:
                if self.check0XY.isChecked():
                    activeFoil.outputFile0XY(self.foilSaveDirectory)
                if self.check0YX.isChecked():
                    activeFoil.outputFile0YX(self.foilSaveDirectory)
                if self.checkX0Y.isChecked():    
                    activeFoil.outputFileX0Y(self.foilSaveDirectory)
                if self.checkXY0.isChecked():
                    activeFoil.outputFileXY0(self.foilSaveDirectory)
                if self.checkY0X.isChecked():
                    activeFoil.outputFileY0X(self.foilSaveDirectory)
                if self.checkYX0.isChecked():
                    activeFoil.outputFileYX0(self.foilSaveDirectory)
    
    def applyFoilExportSettings(self):
        holderFoilList = copy.deepcopy(self.foilList)
        for activeFoil in holderFoilList:
            activeFoil.scale(self.doubleSpinScale.value())
            if self.checkMirrorX.isChecked():
                activeFoil.mirrorX()
            if self.checkMirrorY.isChecked():
                activeFoil.mirrorY()
            if self.radioButtonLE.isChecked() and self.doubleSpinAlpha.value() != 0:
                activeFoil.applyWashout(self.doubleSpinAlpha.value(),0)
            if self.radioButtonTE.isChecked() and self.doubleSpinAlpha.value() != 0:
                activeFoil.applyWashout(self.doubleSpinAlpha.value(),self.doubleSpinScale.value())
        return holderFoilList
    
    def updatePlots(self):
        self.foilPlot1.clear()
        self.foilPlot2.clear()
        self.foilPlot3.clear()
        holderFoilList = self.applyFoilExportSettings()
        if len(holderFoilList) > 0:
            self.foilPlot1.plot(holderFoilList[0].getX(),holderFoilList[0].getY())
            cordinates = ""
            for i in range(len(holderFoilList[0].getX())):
                cordinates = f"{cordinates}{holderFoilList[0].getX()[i]:.4f}\t{holderFoilList[0].getY()[i]:.4f}\n"
            self.cordinateLabel.setText(cordinates)
        if len(holderFoilList) > 1:
            self.foilPlot2.plot(holderFoilList[1].getX(),holderFoilList[1].getY())
        if len(holderFoilList) > 2:
            self.foilPlot3.plot(holderFoilList[2].getX(),holderFoilList[2].getY())   

class foil:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y

    def mirrorX(self):
        self.x = [i * -1 for i in self.x]

    def mirrorY(self):
        self.y = [i * -1 for i in self.y]

    def scale(self, factor):
        self.x = [i * factor for i in self.x]
        self.y = [i * factor for i in self.y]
    
    def applyWashout(self, alpha, axisOfRotation):
        self.xr = []
        self.yr = []
        AlphaRadians = numpy.deg2rad(alpha)
        self.x = [i - axisOfRotation for i in self.x]
        for i in range(len(self.x)):
            self.xr.append(self.x[i]*numpy.cos(AlphaRadians)-self.y[i]*numpy.sin(AlphaRadians))
            self.yr.append(self.y[i]*numpy.cos(AlphaRadians)+self.x[i]*numpy.sin(AlphaRadians))
        self.x = [i + axisOfRotation for i in self.xr]
        self.y = self.yr

    def getX(self):
        return self.x
    
    def getY(self):
        return self.y

    def outputFileXY0(self,location):
        fout = open(f"{location}/{self.name} SW Curve (XY0).txt",'w')
        for i in range(len(self.x)):
            fout.write(f"{self.x[i]:.6f}\t{self.y[i]:.6f}\t0\n")
        fout.close()
    def outputFile0XY(self,location):
        fout = open(f"{location}/{self.name} SW Curve (0XY).txt",'w')
        for i in range(len(self.x)):
            fout.write(f"0\t{self.x[i]:.6f}\t{self.y[i]:.6f}\n")
        fout.close()
    def outputFile0YX(self,location):
        fout = open(f"{location}/{self.name} SW Curve (0YX).txt",'w')
        for i in range(len(self.x)):
            fout.write(f"0\t{self.y[i]:.6f}\t{self.x[i]:.6f}\n")
        fout.close()
    def outputFileX0Y(self,location):
        fout = open(f"{location}/{self.name} SW Curve (X0Y).txt",'w')
        for i in range(len(self.x)):
            fout.write(f"{self.x[i]:.6f}\t0\t{self.y[i]:.6f}\n")
        fout.close()
    def outputFileY0X(self,location):
        fout = open(f"{location}/{self.name} SW Curve (Y0X).txt",'w')
        for i in range(len(self.x)):
            fout.write(f"{self.y[i]:.6f}\t0\t{self.x[i]:.6f}\n")
        fout.close()
    def outputFileYX0(self,location):
        fout = open(f"{location}/{self.name} SW Curve (YX0).txt",'w')
        for i in range(len(self.x)):
            fout.write(f"{self.y[i]:.6f}\t{self.x[i]:.6f}\t0\n")
        fout.close()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()