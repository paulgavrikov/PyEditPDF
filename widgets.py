# partially from https://doc.qt.io/qtforpython/overviews/qtwidgets-widgets-imageviewer-example.html

from PIL import Image
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QScrollArea, QSizePolicy, QHBoxLayout, QPushButton, QGridLayout
from typing import Tuple


def pil2pixmap(im):
    if im.mode == "RGB":
        r, g, b = im.split()
        im = Image.merge("RGB", (b, g, r))
    elif im.mode == "RGBA":
        r, g, b, a = im.split()
        im = Image.merge("RGBA", (b, g, r, a))
    elif im.mode == "L":
        im = im.convert("RGBA")
    im2 = im.convert("RGBA")
    data = im2.tobytes("raw", "RGBA")
    qim = QtGui.QImage(data, im.size[0], im.size[1], QtGui.QImage.Format_ARGB32)
    pixmap = QtGui.QPixmap.fromImage(qim)
    return pixmap


class PageLabel(QtWidgets.QLabel):

    actionEvent = pyqtSignal(str)

    def __init__(self, pil_img, parent=None):
        super().__init__(parent=parent)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setContentsMargins(5, 5, 5, 5)
        self.setScaledContents(True)
        self.set_image(pil_img)

    def set_image(self, pil_img):
        pix_map = pil2pixmap(pil_img)
        self.setPixmap(pix_map)

    def contextMenuEvent(self, event):
        self.menu = QtWidgets.QMenu(self)
        deleteAction = QtWidgets.QAction('Delete', self)
        marginAction = QtWidgets.QAction('Add Margin', self)
        rescaleAction = QtWidgets.QAction('Rescale', self)
        rotateAction = QtWidgets.QAction('Rotate', self)

        deleteAction.triggered.connect(lambda: self.actionEvent.emit("delete"))
        marginAction.triggered.connect(lambda: self.actionEvent.emit("marginAction"))
        rescaleAction.triggered.connect(lambda: self.actionEvent.emit("rescale"))
        rotateAction.triggered.connect(lambda: self.actionEvent.emit("rotate"))

        self.menu.addAction(deleteAction)
        self.menu.addAction(marginAction)
        self.menu.addAction(rescaleAction)
        self.menu.addAction(rotateAction)
        # add other required actions
        self.menu.popup(QtGui.QCursor.pos())


class SelectableImage(QtWidgets.QLabel):

    cropReadyEvent = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.start = (0, 0)
        self.end = (0, 0)
        self.pressed = False

    def get_selection(self) -> Tuple[float, float, float, float]:
        x1, y1, x2, y2 = *self.start, *self.end
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        return x1, y1, x2, y2

    def deselect(self):
        self.start = self.end = (0, 0)

    def get_rel_pos(self, ev: QtGui.QMouseEvent) -> Tuple[float, float]:
        return ev.x() / self.width(), ev.y() / self.height()

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.start = self.end = self.get_rel_pos(ev)
        self.pressed = True

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.end = self.get_rel_pos(ev)
        self.repaint()

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.pressed = False
        self.end = self.get_rel_pos(ev)
        self.cropReadyEvent.emit(self.start != self.end)
        self.repaint()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        if self.start != self.end:
            qp = QPainter()
            qp.begin(self)

            pen = QPen(Qt.black, 2, Qt.DashLine)
            qp.setPen(pen)
            x, y, w, h = *self.start, self.end[0]-self.start[0], self.end[1] - self.start[1]
            x *= self.width()
            y *= self.height()
            w *= self.width()
            h *= self.height()
            qp.drawRect(x, y, w, h)

            qp.end()


class ImageViewer(QtWidgets.QWidget):

    actionEvent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scaleFactor = 1

        self.imageLabel = SelectableImage()
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.imageLabel.cropReadyEvent.connect(lambda ready: self.cropButton.setVisible(ready))

        self.imageScrollArea = QScrollArea()
        self.imageScrollArea.setAlignment(Qt.AlignCenter)
        self.imageScrollArea.setWidget(self.imageLabel)

        self.zoomInButton = QPushButton("+")
        self.zoomInButton.setFixedSize(32, 32)

        self.zoomOutButton = QPushButton("-")
        self.zoomOutButton.setFixedSize(32, 32)

        self.zoomNormalButton = QPushButton("1:1")
        self.zoomNormalButton.setFixedSize(32, 32)

        self.lastButton = QPushButton(">>")
        self.lastButton.setFixedSize(32, 32)

        self.firstButton = QPushButton("<<")
        self.firstButton.setFixedSize(32, 32)

        self.backButton = QPushButton("<")
        self.backButton.setFixedSize(32, 32)

        self.forwardButton = QPushButton(">")
        self.forwardButton.setFixedSize(32, 32)

        self.pageTextEdit = QtWidgets.QTextEdit()
        self.pageTextEdit.setFixedSize(32, 32)
        self.pageTextEdit.setEnabled(False)

        self.cropButton = QPushButton("CROP")
        self.cropButton.setVisible(False)

        self.change_action_bar_visibility(False)

        self.zoomInButton.clicked.connect(lambda: self.scale_image(1.1))
        self.zoomOutButton.clicked.connect(lambda: self.scale_image(0.9))
        self.zoomNormalButton.clicked.connect(lambda: self.normal_size())

        self.firstButton.clicked.connect(lambda: self.actionEvent.emit("first"))
        self.lastButton.clicked.connect(lambda: self.actionEvent.emit("last"))
        self.backButton.clicked.connect(lambda: self.actionEvent.emit("back"))
        self.forwardButton.clicked.connect(lambda: self.actionEvent.emit("forward"))
        self.cropButton.clicked.connect(lambda: self.actionEvent.emit("crop"))

        layout = QGridLayout()
        layout.addWidget(self.imageScrollArea, 1, 0)

        self.actionBar = QHBoxLayout()
        self.actionBar.setContentsMargins(0, 0, 0, 0)

        self.actionBar.addWidget(self.firstButton, 0, Qt.AlignCenter)
        self.actionBar.addWidget(self.backButton, 0, Qt.AlignCenter)
        self.actionBar.addWidget(self.pageTextEdit, 0, Qt.AlignCenter)
        self.actionBar.addWidget(self.forwardButton, 0, Qt.AlignCenter)
        self.actionBar.addWidget(self.lastButton, 0, Qt.AlignCenter)
        self.actionBar.addStretch()
        self.actionBar.addWidget(self.zoomInButton, 0, Qt.AlignCenter)
        self.actionBar.addWidget(self.zoomOutButton, 0, Qt.AlignCenter)
        self.actionBar.addWidget(self.zoomNormalButton, 0, Qt.AlignCenter)
        self.actionBar.addStretch()
        self.actionBar.addWidget(self.cropButton, 0, Qt.AlignCenter)

        layout.addLayout(self.actionBar, 0, 0, )
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

    def get_selection(self):
        return self.imageLabel.get_selection()

    def load_from_pil(self, pil_img):
        pix_map = pil2pixmap(pil_img)
        self.change_image(pix_map)

    def load_from_file(self, path):
        pix_map = QtGui.QPixmap(path)
        self.change_image(pix_map)

    def change_image(self, pix_map):
        self.imageLabel.setPixmap(pix_map)
        self.imageLabel.adjustSize()
        # self.cropButton.setVisible(False)
        self.change_action_bar_visibility(True)
        self.scale_image(1)

    def change_action_bar_visibility(self, on):
        self.lastButton.setVisible(on)
        self.firstButton.setVisible(on)
        self.forwardButton.setVisible(on)
        self.backButton.setVisible(on)
        self.zoomInButton.setVisible(on)
        self.zoomOutButton.setVisible(on)
        self.zoomNormalButton.setVisible(on)
        self.pageTextEdit.setVisible(on)

    def normal_size(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1

    def fit_to_window(self, on):
        self.imageScrollArea.setWidgetResizable(on)
        if not on:
            self.normal_size()

    def _adjust_scroll_bar(self, scroll_bar, factor):
        scroll_bar.setValue(int(factor * scroll_bar.value() + ((factor - 1) * scroll_bar.pageStep() / 2)))

    def scale_image(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self._adjust_scroll_bar(self.imageScrollArea.horizontalScrollBar(), factor)
        self._adjust_scroll_bar(self.imageScrollArea.verticalScrollBar(), factor)
