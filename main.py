#from locale import ABMON_10
import sys
from PyQt5 import QtWidgets, QtCore, QtGui, QtPrintSupport, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QFileDialog, QGraphicsView
from numpy import linspace, cos, sin, pi, ceil, floor, arange
import pyqtgraph as pg
import numpy as np
import pandas as pp
from layout import Ui_MainWindow
from scipy import signal






class MainWindow(QtWidgets.QMainWindow):
    spectrogramImgageList = [None, None, None]

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.Signal_compose_widget.showGrid(x=True, y=True)
        self.ui.Signal_Summ_widget.showGrid(x=True, y=True)
        self.ui.Samplingpoints_widget.showGrid(x=True, y=True)
        self.ui.Sampledsignal_widget.showGrid(x=True, y=True)

        #   initialize variables    #     #     #

        self.fmax = 0
        self.freq_arr = []
        self.y_sampled = [] 
        self.y=[]
        self.x_axis_limit = 900
        self.step = 0
        self.time = np.arange(0,self.x_axis_limit)
        self.time_sampled = np.arange(0,self.x_axis_limit)
        self.max_num_of_samples = 0
        self.signalsname = ""
        self.ampmax = 0
        self.amplist = []
        self.signals_components = []
        self.tmin = -3
        self.tmax = 3
        self.composer_time_axis = linspace(self.tmin, self.tmax, self.x_axis_limit)

        

        #   connecting UI elements    #     #     #
        self.ui.Compose_pushButton.clicked.connect(lambda: self.composer())
        self.ui.comboBox_Signals.currentIndexChanged.connect(lambda: self.composerchanging())
        self.ui.pushButton_Addsignal.clicked.connect(lambda: self.composerSum())
        self.ui.pushButton_Delete.clicked.connect(lambda: self.delete_signal())
        self.ui.Points_sampled_horizontalSlider.valueChanged.connect(lambda: self.update_plots())
        self.ui.Clear_pushButton.clicked.connect(lambda: self.clear())
        self.ui.Confirmtosampling_pushButton.clicked.connect(lambda: self.Send_to_sampler())
        self.ui.Upload_pushButton.clicked.connect(lambda: self.open())



    def update_plots(self): 
        if len(self.y) == 0:
            return

        self.ui.Samplingpoints_widget.clear()
        self.ui.Samplingpoints_widget.plot(self.time, self.y, pen='b')
        self.num_of_samples = self.ui.Points_sampled_horizontalSlider.value() *6 +1
        self.ui.num_of_samples_lcd.display(round(self.num_of_samples))
        print(self.num_of_samples/ (   6* (2/3 * self.max_num_of_samples)   )   )
        print("num of samples : " + str(self.num_of_samples))
        print("self.max num of sampples : " + str(self.max_num_of_samples))
        self.ui.percentage_of_fmax_lcd.display("{:.1f}".format(self.num_of_samples/ (   3* (2/3 * self.max_num_of_samples)  ) ))
        self.y_sampled = [] ## ## ##


        # DOWNSAMPLING
        # some sampling function in scipy module :
        #   signal.resample(self.y, samples), signal.decimate(self.y,samples)
        #   sampling by choosing a certain indices and appending correponding values to y_sampled
        self.step = int(len(self.y)/self.num_of_samples)
        self.time_sampled = np.arange(0,len(self.y),self.step)
        for i in self.time_sampled:
            self.y_sampled = np.append(self.y_sampled, self.y[i])



        #plotting the original signal with its sampled points  
        self.ui.Samplingpoints_widget.plot(self.time_sampled, self.y_sampled, symbol='o', pen=None)
        
        if len(self.y_sampled) > 1:
            self.sinc_interpolation()
            self.ui.Sampledsignal_widget.clear()
            self.ui.Sampledsignal_widget.plot( np.arange(0,len(self.y)), self.reconstructed_signal, pen='r')

    def composerchanging(self):
        self.ui.Signal_compose_widget.clear()
        index = self.ui.comboBox_Signals.currentIndex()
        signal_part = self.signals_components[index]
        self.ui.Signal_compose_widget.plot(self.composer_time_axis, signal_part, pen='r')
        self.ui.Signal_compose_widget.setLimits(xMin=self.tmin - 0.2, xMax=self.tmax + 0.2, yMin=-self.amplist[index] - 0.2,
                                                yMax=self.amplist[index] + 0.2)

    def composer(self):
        self.ui.Signal_compose_widget.clear()
        freq = self.ui.SpinBox_Frequency.value()
        self.freq_arr.append(freq) # for sampling

        self.amp = self.ui.SpinBox_Magnitude.value()
        self.ui.Signal_compose_widget.setLimits(xMin=self.tmin - 0.2, xMax=self.tmax + 0.2, yMin=-self.amp - 0.2, yMax=self.amp + 0.2)
        phase = self.ui.SpinBox_Phase.value()
        signal_part = self.amp * sin(2 * pi * freq * self.composer_time_axis + phase)
        self.signals_components.append(signal_part)
        self.amplist.append(self.amp)
        self.signalsname = self.ui.Signal_name_lineEdit.text()
        self.ui.comboBox_Signals.addItem(self.signalsname)
        self.ui.Signal_compose_widget.plot(self.composer_time_axis, signal_part, pen='y')
        self.ampmax += self.amp
        self.ui.comboBox_Signals.setCurrentIndex(len(self.amplist) - 1)
        SavedSignal = np.asarray([np.round(self.composer_time_axis, 3), np.round(sum(self.signals_components), 3)])
        np.savetxt(str(self.signalsname) + '.csv', SavedSignal.T, fmt='%1.5f', delimiter=",", header="t,x")

    def composerSum(self):
        
        self.ui.Signal_Summ_widget.setLimits(xMin=self.tmin - 0.2, xMax=self.tmax + 0.2, yMin=-self.ampmax - 0.2, yMax=self.ampmax + 0.2)
        self.ui.Signal_Summ_widget.clear()
        self.ui.Signal_Summ_widget.plot(self.composer_time_axis, sum(self.signals_components), pen='g')

    def delete_signal(self):
        self.ui.comboBox_Signals.removeItem(self.ui.comboBox_Signals.currentIndex())
        self.signals_components.pop(self.ui.comboBox_Signals.currentIndex())
        self.ampmax -= self.amplist[self.ui.comboBox_Signals.currentIndex()]
        self.amplist.pop(self.ui.comboBox_Signals.currentIndex())
        self.composerSum()

    def Send_to_sampler(self):
        self.y = sum(self.signals_components)
        self.set_slider_limits()
        self.set_graph_limits()
        self.update_plots()
        self.ui.tabWidget.setCurrentIndex(0)

        
    def set_graph_limits(self):
        if len(self.y) == 0:
            return
        #multiply by 1.25 for padding
        self.ui.Samplingpoints_widget.setLimits(xMin = 0 ,xMax=self.x_axis_limit,yMin = min(self.y)*1.25 ,yMax=max(self.y)*1.25)
        self.ui.Sampledsignal_widget.setLimits(xMin = 0 ,xMax=self.x_axis_limit,yMin = min(self.y)*1.25,yMax=max(self.y)*1.25)

    def clear(self):
        self.ui.Sampledsignal_widget.clear()
        self.ui.Samplingpoints_widget.clear()
        self.y = []
        
    def sinc_interpolation(self):
        # resources for understanding sinc inerpolation
        # https://youtu.be/VsQc9tY-FT0  |   https://youtu.be/W52hrvnjVOk
        self.sinc_magnitude = np.tile(self.time, (len(self.time_sampled), 1)) - np.tile(
                                            self.time_sampled[:, np.newaxis], (1, len(self.time)))
        self.reconstructed_signal = np.dot(self.y_sampled, np.sinc(self.sinc_magnitude / self.step))
        

    def open(self):
        global data
        path = QFileDialog.getOpenFileName(self, 'Open a file', '', 'All Files (*.*)')
        if path != ('', ''):
            data = path[0]
        data1 = pp.read_csv(data)
        t = data1['# t']
        x = data1['x']
        self.y = x
        self.time = np.arange(0,len(self.y))
        self.set_slider_limits()
        self.set_graph_limits()
        self.update_plots()

    def set_slider_limits(self):
        # to set constrain to the slider //from 0 to 3fmax
        if len(self.y) == 0:
            return

        signal_fft = np.fft.rfft(self.y)
        peak = np.argmax(signal_fft)
        self.fmax = np.abs(peak)
        
        self.max_num_of_samples =0.5 * self.fmax

        self.ui.Points_sampled_horizontalSlider.setMinimum(1)
        self.ui.Points_sampled_horizontalSlider.setMaximum(self.max_num_of_samples)#0.5

        
def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()