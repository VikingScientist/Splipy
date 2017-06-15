import sys
import os
from OpenGL.GL import *
from OpenGL.GLU import *
# from PyQt5.QtWidgets import QWidget, QApplication, QPushButton, QHBoxLayout, QAction, qApp, QMainWindow, QFileDialog
from PyQt5.QtWidgets import *
from PyQt5 import QtGui, QtCore
from PyQt5.QtOpenGL import *
from splipy import *
from splipy.IO import *
import numpy as np

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.widget = glWidget(self)

        # self.button = QPushButton('Test', self)

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.widget)
        # mainLayout.addWidget(self.button)

        self.setLayout(mainLayout)

        ### add menu
        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        openAction = QAction('&Open file', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.show_open_dialog)

        menubar  = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)

        self.setGeometry(600,600, 800,600)
        self.setWindowTitle('Splipy viewer')

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.widget.update)
        timer.start(20)

    def show_open_dialog(self, filename):
        # defaults to home directory... might change this to current directory later
        fname = QFileDialog.getOpenFileName(self, 'Open file', os.environ['HOME'], 'Geometry (*.g2)')
        if fname[0]:
            self.open_file(fname[0])

    def open_file(self, filename):
        print('Opening file %s'%(filename))
        with G2(filename) as f:
            self.spline_model = f.read()

        self.widget.tesselate(self.spline_model)



class glWidget(QGLWidget):

    def __init__(self, parent):
        QGLWidget.__init__(self, parent)
        self.setMinimumSize(640, 480)
        self.quad_x = []
        self.quad_n = []
        self.quad_i = []

        self.line_x = []
        self.line_i = []
        self.t = 0


    def tesselate(self, model):
        print('tesselating now')
        for s in model:
            if isinstance(s,Volume):
                faces = s.faces()
                faces[1].swap()
                faces[2].swap()
                faces[5].swap()
                self.tesselate(faces)
            else:
                u = np.linspace(s.start('u'), s.end('u'), 40)
                v = np.linspace(s.start('v'), s.end('v'), 40)
                x = s(u,v)
                n = s.normal(u,v)
                self.quad_x.append(x)
                self.quad_n.append(n)
                indices = []
                for i in range(39):
                    for j in range(39):
                        indices.append(  i  *40 +  j  );
                        indices.append((i+1)*40 +  j  );
                        indices.append((i+1)*40 +(j+1));
                        indices.append(  i  *40 +(j+1));
                self.quad_i.append(np.array(indices, dtype=np.uint32))

                u = s.knots('u')
                v = np.linspace(s.start('v'), s.end('v'), 40)
                x = s(u,v)
                for i in range(x.shape[0]):
                    self.line_x.append(x[i,:])

                u = np.linspace(s.start('u'), s.end('u'), 40)
                v = s.knots('v')
                x = s(u,v)
                for i in range(x.shape[1]):
                    self.line_x.append(x[:,i])


    def paintGL(self):
        print('paintGL')
        self.t += 0.015
        glViewport(0,0,640,480)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        gluLookAt(2.5*np.cos(self.t),2.5*np.sin(self.t),1.0,  0,0,0,  0,0,1)

        glEnable(GL_LIGHTING)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glColor3f(76/255, 176/255, 196/255)
        for i in range(len(self.quad_x)):
            glVertexPointer(3, GL_DOUBLE, 0, self.quad_x[i])
            glNormalPointer(   GL_DOUBLE, 0, self.quad_n[i])
            glDrawElements(GL_QUADS, int(len(self.quad_i[i])), GL_UNSIGNED_INT, self.quad_i[i])
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisable(GL_LIGHTING)

        glLineWidth(2)
        glColor3f(0,0,0)
        for i in range(len(self.line_x)):
            glVertexPointer(3, GL_DOUBLE, 0, self.line_x[i])
            glDrawArrays(GL_LINE_STRIP, 0, len(self.line_x[i]))
        glDisableClientState(GL_VERTEX_ARRAY)


        glFlush()


    def initializeGL(self):
        glClearDepth(1.0)
        glClearColor(1,1,1,0)
        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(50.0,1.33,0.01, 100.0)
        glMatrixMode(GL_MODELVIEW)

        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [.3, .3, .3, 1.0])
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [.8, .8, .8, 1.])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [ 1,  1,  1, 1 ])
        glLightfv(GL_LIGHT0, GL_POSITION, [2, -1, -4, 0])  # last value=0, directional light
        glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
        glLightfv(GL_LIGHT1, GL_DIFFUSE,  [.5, .5, .5, 1.])
        glLightfv(GL_LIGHT1, GL_SPECULAR, [.3, .3, .3, 1 ])
        glLightfv(GL_LIGHT1, GL_POSITION, [-14,-7,-28,1])  # last value=1, positional light
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    if(len(sys.argv) > 1):
        window.open_file(sys.argv[1])

    window.show()
    app.exec_()

