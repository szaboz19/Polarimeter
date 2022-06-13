import PyQt5.sip

import sys 
import time

from rotator_gui import Ui_Form
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc

import serial, serial.tools.list_ports

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class MyApp(qtw.QWidget):
    	
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Init stuff
        self.port_det = serial.Serial()
        self.port_rot = serial.Serial()
        self.rotator_angle = 0
        self.meas_angle_data = []
        self.meas_det_data = []
        
        self.ui.DetRngList.addItems(['Auto','1','2','3','4','5'])
        self.ui.DetRngList.setCurrentIndex(5)
        self.ui.DetChList.addItems(['A','B'])
        self.ui.DetModeList.addItems(['I','U'])
        self.ui.DetAvgEdit.setText('1')
        self.ui.RangeBar.setValue(0)
        self.ui.RangeBar.setStyleSheet("QProgressBar::chunk "
                          "{"
                          "background-color: green;"
                          "}")
        
        self.RangeBarMin=2E-6
        self.RangeBarMax=200E-6
        self.ui.BarMinLabel.setText("{:.2e}".format(self.RangeBarMin))
        self.ui.BarMaxLabel.setText("{:.2e}".format(self.RangeBarMax))
        
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.ui.verticalLayout_7.replaceWidget(self.ui.GraphWidget, self.canvas)    # GraphWidget was just a dummy placeholder
        self.reference_plot = None
        
        # self.canvas.axes.plot([1,2,3,4,5],[10,12,16,18,30], "bo-")       # plot data like this!
        
        
        self.updatePorts()        
        
        
        # Event stuff
        self.ui.ConnectDetBtn.clicked.connect(self.connect_Det_serial)
        self.ui.ConnectRotBtn.clicked.connect(self.connect_Rot_serial)
        self.ui.RefreshPortsBtn.clicked.connect(self.updatePorts)
        self.ui.RotLeftFastBtn.clicked.connect(self.manualRotate)
        self.ui.RotLeftSlowBtn.clicked.connect(self.manualRotate)
        self.ui.RotRightFastBtn.clicked.connect(self.manualRotate)
        self.ui.RotRightSlowBtn.clicked.connect(self.manualRotate)
        self.ui.ZeroBtn.clicked.connect(self.zeroRotator)
        self.ui.StartLiveBtn.clicked.connect(self.liveData)
        self.ui.StartMeasBtn.clicked.connect(self.measurement)
        self.ui.SaveDataBtn.clicked.connect(self.saveData)
        self.ui.SaveImageBtn.clicked.connect(self.saveImage)
    
    
    
    # my function definitions
        
    def connect_Det_serial(self):
        if (self.ui.ConnectDetBtn.isChecked()):
            self.port_det_name = self.ui.DetPortList.currentText()
            self.port_det_baudrate = 19200
            try:
                self.port_det = serial.Serial(self.port_det_name, self.port_det_baudrate, timeout=0.1, write_timeout=0.1)
                #print("try to connect")
            except:
                print("ERROR with connection")
            
            if(self.port_det.isOpen() ):
                #print("detector connected")
                self.ui.ConnectDetBtn.setText("Connected")
                time.sleep(2)
                message = self.port_det.readline()
                print(message)
                self.livedataworker = LiveDataWorkerThread(self.port_det)
                if(self.port_rot.isOpen()):
                    self.measurementworker = MeasurementDataWorkerThread(self.port_det, self.port_rot)
            else:
                self.ui.ConnectDetBtn.setChecked(False)
                #print("det not connected")
        else:
            self.port_det.close()
            self.ui.ConnectDetBtn.setText("Connect")
            # print("detector disconnected")
            # stop live measure
            # stop measure
            
    
    def connect_Rot_serial(self):       # a fent levő teljes fszságot idemásolni rotor-gombokkal és miegymással
        if (self.ui.ConnectRotBtn.isChecked()):
            self.port_rot_name = self.ui.RotPortList.currentText()
            self.port_rot_baudrate = 57600
            try:
                self.port_rot = serial.Serial(self.port_rot_name, self.port_rot_baudrate, timeout=0.1, write_timeout=0.1)
                #print("try to connect")
            except:
                print("ERROR with connection")
            
            if(self.port_rot.isOpen() ):
                #print("rotator connected")
                self.ui.ConnectRotBtn.setText("Connected")
                time.sleep(2)
                message = self.port_rot.readline()
                print(message)
                self.askRotForAngle()
                if(self.port_det.isOpen()):
                    self.measurementworker = MeasurementDataWorkerThread(self.port_det, self.port_rot)
            else:
                self.ui.ConnectRotBtn.setChecked(False)
                #print("rot not connected")
        else:
            self.port_rot.close()
            self.ui.ConnectRotBtn.setText("Connect")
            # print("rotator disconnected")
            # stop measure
        
    
    def send_data(self):
        print("sending data")
    
    def read_data(self):
        print("reading data")
        
    def updatePorts(self):
        self.portList = [port.device for port in list(serial.tools.list_ports.comports())]
        self.ui.DetPortList.clear()
        self.ui.DetPortList.addItem('')
        self.ui.DetPortList.addItems(self.portList)
        
        self.ui.RotPortList.clear()
        self.ui.RotPortList.addItem('')
        self.ui.RotPortList.addItems(self.portList)
    
    
    def manualRotate(self):         ### ezeket kell átírni serial-send-re, esetleg vizsgálni, hogy legális-e a forgatás éppen most
        sender = self.sender().text()
        if(self.port_rot.isOpen() ):
            if(sender == "<<"):
                print("rotating fast left")
                self.port_rot.write(b'SRA %f \r\n' % (self.rotator_angle-10))
            elif(sender == "<"):
                print("rotating slow left")
                self.port_rot.write(b'SRA %f \r\n' % (self.rotator_angle-1))
            elif(sender == ">"):
                print("rotating slow right")
                self.port_rot.write(b'SRA %f \r\n' % (self.rotator_angle+1))
            elif(sender == ">>"):
                print("rotating fast right")
                self.port_rot.write(b'SRA %f \r\n' % (self.rotator_angle+10))
            
            time.sleep(0.5)
            self.askRotForAngle()



    def zeroRotator(self):
        if(self.port_rot.isOpen() ):
            self.port_rot.write(b'ZERO\r\n')
            
            time.sleep(0.1)
            self.askRotForAngle()
            


    def askRotForAngle(self):
        self.port_rot.write(b'GRA\r\n')
        time.sleep(0.1)
        message = self.port_rot.readline()
        if (message!=b''):
            self.rotator_angle = float(message)
            self.ui.RotAngLCD.display(self.rotator_angle)
    
    
    
    
    
    def liveData(self):
        if(self.ui.StartLiveBtn.isChecked()):
            if(self.port_det.isOpen()): 
               #print("live is started")
               self.ui.StartLiveBtn.setText("Live data is running")
               #start liveData_thread...
               self.startLiveData()
            else:
                self.ui.StartLiveBtn.setChecked(False)
            
        else:
            self.ui.StartLiveBtn.setText("Start Live")
            self.stopLiveData()

    


    def startLiveData(self):
        
        det_channel = self.ui.DetChList.currentText()
        det_mode = self.ui.DetModeList.currentText()
        det_avg = self.ui.DetAvgEdit.text()
        det_range = self.ui.DetRngList.currentText()
        if(det_range== "Auto"):
            det_range = "0"    
        
        self.port_det.write(b'CH%b\r' % det_channel.encode())      # Channel A or B
        time.sleep(0.1)
        self.port_det.write(b'M%b\r' % det_mode.encode())       # Current or Voltage mode
        time.sleep(0.1)
        self.port_det.write(b'A %b\r' % det_avg.encode())      # average of measurements
        time.sleep(0.1)
        self.port_det.write(b'R %b\r' % det_range.encode())      # range: 5 - 200 uA
        time.sleep(0.1)
        
        self.RangeBarMax = 2e-10*10**int(det_range)
        self.RangeBarMin = 2e-12*10**int(det_range)
        self.ui.RangeBar.setStyleSheet("QProgressBar::chunk "
                      "{"
                      "background-color: green;"
                      "}")

        self.livedataworker.start()
        self.livedataworker.incomingData.connect(self.updateLiveDataLCD)



    def stopLiveData(self):
        self.livedataworker.stop()

            

    def updateLiveDataLCD(self, val): #and RangeBar
        self.ui.DetDataLCD.display(val)
        if(self.ui.DetRngList.currentText() != "Auto"):
            rangeSet = float(self.ui.DetRngList.currentText())
        
        if(val>self.RangeBarMax*0.9505):
            self.RangeBarMax = self.RangeBarMax*10
            self.RangeBarMin = self.RangeBarMin*10
            self.ui.BarMinLabel.setText("{:.2e}".format(self.RangeBarMin))
            self.ui.BarMaxLabel.setText("{:.2e}".format(self.RangeBarMax))
            
            if(self.RangeBarMax>=2.02e-9*10**rangeSet):
                self.ui.RangeBar.setStyleSheet("QProgressBar::chunk "
                              "{"
                              "background-color: red;"
                              "}")
            else:
                self.ui.RangeBar.setStyleSheet("QProgressBar::chunk "
                              "{"
                              "background-color: green;"
                              "}")
            
                        
        elif(val<self.RangeBarMin*5.95):
            self.RangeBarMax = self.RangeBarMax/10
            self.RangeBarMin = self.RangeBarMin/10
            self.ui.BarMinLabel.setText("{:.2e}".format(self.RangeBarMin))
            self.ui.BarMaxLabel.setText("{:.2e}".format(self.RangeBarMax))
            
            if(self.RangeBarMin<1.98e-12*10**rangeSet):
                self.ui.RangeBar.setStyleSheet("QProgressBar::chunk "
                              "{"
                              "background-color: red;"
                              "}")
            else:
                self.ui.RangeBar.setStyleSheet("QProgressBar::chunk "
                              "{"
                              "background-color: green;"
                              "}")
                         
        self.ui.RangeBar.setValue(int((val-self.RangeBarMin)/(self.RangeBarMax-self.RangeBarMin)*100))
        






    def measurement(self):
        if(self.ui.StartMeasBtn.isChecked()):
            if(self.port_det.isOpen() and self.port_rot.isOpen()): 
               # print("measurement is started")
               self.ui.StartMeasBtn.setText("Measurement is running")
               self.startmeasurement()
               
            else:
                self.ui.StartMeasBtn.setChecked(False)
            
        else:
            self.ui.StartMeasBtn.setText("Start Measurement")
            self.stopmeasurement()



    def startmeasurement(self):
        
        # clear data
        self.meas_angle_data = []
        self.meas_det_data = []
        self.canvas.axes.clear()
        
        # setup PCM 
        det_channel = self.ui.DetChList.currentText()
        det_mode = self.ui.DetModeList.currentText()
        det_avg = self.ui.DetAvgEdit.text()
        det_range = self.ui.DetRngList.currentText()
        if(det_range== "Auto"):
            det_range = "0"    
        
        self.port_det.write(b'CH%b\r' % det_channel.encode())      # Channel A or B
        time.sleep(0.1)
        self.port_det.write(b'M%b\r' % det_mode.encode())       # Current or Voltage mode
        time.sleep(0.1)
        self.port_det.write(b'A %b\r' % det_avg.encode())      # average of measurements
        time.sleep(0.1)
        self.port_det.write(b'R %b\r' % det_range.encode())      # range: 5 - 200 uA
        time.sleep(0.1)
        
        # setup Rotator
        self.measurementworker.startangle = float(self.ui.RotStartEdit.text())
        self.measurementworker.stopangle = float(self.ui.RotStopEdit.text())
        self.measurementworker.stepangle = float(self.ui.RotStepEdit.text())

        self.measurementworker.wait_for_meas= float(det_avg)*0.125

        self.measurementworker.start()
        self.measurementworker.incomingData.connect(self.updateGraph)
        self.measurementworker.finished.connect(self.measurement_finished)


    def stopmeasurement(self):
        self.measurementworker.stop()



    def updateGraph(self, values):
        self.meas_angle_data.append(values[0])
        self.meas_det_data.append(values[1])
        self.canvas.axes.plot(self.meas_angle_data, self.meas_det_data, "bo-")
        self.canvas.draw()
        self.ui.RotAngLCD.display(values[0])
        self.updateLiveDataLCD(values[1])



    def measurement_finished(self):
        self.ui.StartMeasBtn.setChecked(False)
        self.ui.StartMeasBtn.setText("Start Measurement")
        # print("finished")






    def saveData(self):
    
        fname = qtw.QFileDialog.getSaveFileName(self, 'Save file', 'eredmeny', 'CSV Files (*.csv)')
                
        if (fname[0]!=""):
            f = open(fname[0], 'w')
            if(self.ui.DetModeList.currentText()=="I"):
                signal = "A"
            else:
                signal = "V"
            f.write('angle [deg]; detector signal ['+ signal +']\n')
            for i in range(len(self.meas_angle_data)):
                f.write(str(self.meas_angle_data[i])+'; '+str(self.meas_det_data[i])+'\n')
        
            f.close


    def saveImage(self):
        fname = qtw.QFileDialog.getSaveFileName(self, 'Save image', 'eredmeny', 'PNG Files (*.png)')
                
        if (fname[0]!=""):
            self.canvas.figure.savefig(fname[0])








    
    def closeEvent(self,e):
        
        # if meas_thread is running: close meas_thread
        try:
            if(self.livedataworker.running==True):
                self.livedataworker.stop()
        except:
            pass
        if(self.port_det.isOpen()): 
            self.port_det.close()
        if(self.port_rot.isOpen()): 
            self.port_rot.close()







class LiveDataWorkerThread(qtc.QThread):
    incomingData = qtc.pyqtSignal(float)
    def __init__(self, serialport):
        qtc.QThread.__init__(self)
        self.serialport = serialport
        self.running = True
    
    def run(self):
        #print("starting thread...")
        self.serialport.write(b'C\r')
        while(True):
            data = self.serialport.readline()
            if(len(data)>0): # csak ez így nem ok, mert mikor konvertáljuk számmá? hogy nézzük meg hogy valid-e?
                try:
                    self.incomingData.emit(float(data))
                    #print(float(data))
                except:
                    pass
            #time.sleep(0.05)
   
    def stop(self):
        self.running = False
        #print('Stopping thread...')
        self.serialport.write(b'H\r')
        self.terminate()
    



class MeasurementDataWorkerThread(qtc.QThread):
    incomingData = qtc.pyqtSignal(list)
    def __init__(self, serialport_det, serialport_rot):
        qtc.QThread.__init__(self)
        self.serialport_det = serialport_det
        self.serialport_rot = serialport_rot
        self.running = True
        self.startangle = 0.0
        self.stopangle = 0.0
        self.stepangle = 0.0
        self.wait_after_moving = 0.0
        self.wait_for_meas = 0.0
    
    def run(self):
        # print("starting thread...")
        
        # ide kerül a mérési szekvencia, start-stop-step, measure...
        # hol van most?
        self.serialport_rot.write(b'GRA\r\n')
        # time.sleep(1)
        message = self.serialport_rot.readline()
        position = float(message)
        # mozogjon a start elé kicsivel
        self.serialport_rot.write(b'SRA %f \r\n' % (self.startangle-2*self.stepangle))   # start just before the starting angle because of the backlash
        moving=True
        while (moving):
            time.sleep(0.2)
            pre_pos = position
            self.serialport_rot.write(b'GRA\r\n')
            message = self.serialport_rot.readline()
            position = float(message)
            # print("current position: ", position)
            if (position==pre_pos):
                moving=False
        
        time.sleep(1)
        self.wait_after_moving = 0.1*self.stepangle
        
        
        for i in range(int((self.stopangle-self.startangle)/self.stepangle)+1):
            # move to next position
            self.serialport_rot.write(b'SRA %f \r\n' % (self.startangle+i*self.stepangle))
            time.sleep(self.wait_after_moving)
            # print("wait after moving", self.wait_after_moving)
            
            # ask for exact position
            self.serialport_rot.write(b'GRA\r\n')
            message = self.serialport_rot.readline()
            position = float(message)
            print(position)
            
            # measure detector
            self.serialport_det.write(b'M 1\r')
            time.sleep(self.wait_for_meas)
            message = self.serialport_det.readline()
            endmessage = self.serialport_det.readline()
            meas = float(message)
            
            values = [position, meas]
            self.incomingData.emit(values)
            
        
  
    def stop(self):
        self.running = False
        # print('Stopping thread...')
        self.terminate()






class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi = dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        fig.tight_layout()





if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    
    w = MyApp()
    w.show()
    
    sys.exit(app.exec_())   
    