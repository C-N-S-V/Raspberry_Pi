import sys
import collections
import numpy as np

from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

import board
import busio
import adafruit_fxos8700
import adafruit_fxas21002c
import imufusion


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Setup I2C
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.fxos = adafruit_fxos8700.FXOS8700(self.i2c)
        self.fxas = adafruit_fxas21002c.FXAS21002C(self.i2c, gyro_range=adafruit_fxas21002c.GYRO_RANGE_2000DPS)

        # Setup AHRS
        self.ahrs = imufusion.Ahrs()
        sample_rate = 100  # Hz
        self.ahrs.settings = imufusion.Settings(10, 10, 20, 5 * sample_rate)

        # Setup graph
        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)
        self.i = 0
        self.time_data = collections.deque([], 20)
        self.euler_x = collections.deque([], 20)
        self.euler_y = collections.deque([], 20)
        self.euler_z = collections.deque([], 20)

        self.graphWidget.setBackground(QtGui.QColor(255, 255, 255, 255))
        self.graphWidget.setYRange(-180, 180)
        self.graphWidget.setLabels(bottom="time (s)", left="euler angles (deg)")
        self.graphWidget.getAxis('left').setTickSpacing(major=90, minor=10)
        self.graphWidget.showGrid(x=True, y=True)

        pen_x = pg.mkPen(color=(255, 0, 0), width=2, style=QtCore.Qt.SolidLine)
        pen_y = pg.mkPen(color=(0, 255, 0), width=2, style=QtCore.Qt.SolidLine)
        pen_z = pg.mkPen(color=(0, 0, 255), width=2, style=QtCore.Qt.SolidLine)

        self.data_line_x = self.graphWidget.plot(self.time_data, self.euler_x, pen=pen_x)
        self.data_line_y = self.graphWidget.plot(self.time_data, self.euler_y, pen=pen_y)
        self.data_line_z = self.graphWidget.plot(self.time_data, self.euler_z, pen=pen_z)

        # Setup timer
        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

    def update_plot_data(self):
        self.time_data.append(self.i * 0.01)

        gyroscope = np.array(self.fxas.gyroscope)
        accelerometer = np.array(self.fxos.accelerometer)
        magnetometer = np.array(self.fxos.magnetometer)

        self.ahrs.update(gyroscope, accelerometer, magnetometer, 1 / 100)

        euler = self.ahrs.quaternion.to_euler()
        self.euler_x.append(euler[0])
        self.euler_y.append(euler[1])
        self.euler_z.append(euler[2])

        self.data_line_x.setData(self.time_data, self.euler_x)
        self.data_line_y.setData(self.time_data, self.euler_y)
        self.data_line_z.setData(self.time_data, self.euler_z)
        self.i += 1


app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.show()
sys.exit(app.exec_())
