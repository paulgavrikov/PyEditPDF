from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QListWidgetItem
from widgets import ImageViewer, PageLabel

## Controller Imports
from reportlab.pdfgen.canvas import Canvas
from pdfrw import PdfReader, PdfWriter, PageMerge
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl
from pdf2image import convert_from_bytes
import os


class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(920, 640)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QtWidgets.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.pageScrollArea = QtWidgets.QListWidget(self.splitter)
        self.pageScrollArea.setStyleSheet("QListView::item { height: 100px; }")

        ####

        self.previewArea = ImageViewer(self.splitter)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.previewArea.sizePolicy().hasHeightForWidth())
        self.previewArea.setSizePolicy(sizePolicy)
        self.previewArea.setObjectName("previewArea")

        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionOpenPages = QtWidgets.QAction(MainWindow)
        self.actionOpenPages.setObjectName("actionOpenPages")
        self.actionAddPages = QtWidgets.QAction(MainWindow)
        self.actionAddPages.setObjectName("actionOpenPages")
        self.actionSave = QtWidgets.QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSaveAs = QtWidgets.QAction(MainWindow)
        self.actionSaveAs.setObjectName("actionSaveAs")
        self.actionEditMeta = QtWidgets.QAction(MainWindow)
        self.actionEditMeta.setObjectName("actionEditMeta")

        self.actionSave.setEnabled(False)
        self.actionSaveAs.setEnabled(False)
        self.actionAddPages.setEnabled(False)
        self.actionEditMeta.setEnabled(False)

        self.menuFile.addAction(self.actionOpenPages)
        self.menuFile.addAction(self.actionAddPages)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addAction(self.actionEditMeta)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "PyEditPDF"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionOpenPages.setText(_translate("MainWindow", "Open Page(s)"))
        self.actionOpenPages.setShortcut(_translate("MainWindow", "Ctrl+O"))
        self.actionAddPages.setText(_translate("MainWindow", "Add Page(s)"))
        self.actionAddPages.setShortcut(_translate("MainWindow", "Ctrl+Shift+O"))
        self.actionSave.setText(_translate("MainWindow", "Save"))
        self.actionSave.setShortcut(_translate("MainWindow", "Ctrl+S"))
        self.actionSaveAs.setText(_translate("MainWindow", "Save As"))
        self.actionSaveAs.setShortcut(_translate("MainWindow", "Ctrl+Shift+S"))
        self.actionEditMeta.setText(_translate("MainWindow", "Edit Meta"))
        self.actionEditMeta.setShortcut(_translate("MainWindow", "Ctrl+M"))


class Controller:

    def handle_item_click(self, clicked):
        for i in range(len(ui.pageScrollArea)):
            if clicked == ui.pageScrollArea.item(i):
                self.show_page(i)
        clicked.setSelected(True)

    def handle_action(self, action: str):
        print(action)
        if action == "forward":
            if self.current_page < len(self.pages) - 1:
                self.show_page(self.current_page + 1)
        elif action == "back":
            if self.current_page > 0:
                self.show_page(self.current_page - 1)
        elif action == "first":
            self.show_page(0)
        elif action == "last":
            self.show_page(len(self.pages) - 1)
        elif action == "crop":
            selection = ui.previewArea.get_selection()

            info = PageMerge().add(self.pages[self.current_page])
            x1, y1, x2, y2 = info.xobj_box

            crop_section = x1 + selection[0] * (x2 - x1), y1 + selection[1] * (y2 - y1), \
                           x1 + selection[2] * (x2 - x1), y1 + selection[3] * (y2 - y1)

            crop_section = (crop_section[0], crop_section[1], crop_section[2] - crop_section[0], crop_section[3] - crop_section[1])

            new_page = self.crop_page(self.pages[self.current_page], crop_section)
            self.pages[self.current_page] = new_page
            self.renders[self.current_page] = self.page_to_img(new_page)

            ui.previewArea.load_from_pil(self.renders[self.current_page])
            ui.pageScrollArea.itemWidget(ui.pageScrollArea.item(self.current_page)).set_image(self.renders[self.current_page])

            ui.previewArea.imageLabel.deselect()
            ui.previewArea.cropButton.setVisible(False)

            self.set_saved(False)
        elif action == "delete":
            self.delete_selected()
        elif action == "margin":
            pass
        elif action == "rotate":
            self.rotate_selected()
        elif action == "rescale":
            pass

    def delete_selected(self):
        for model_idx in sorted(list(ui.pageScrollArea.selectedIndexes()), reverse=True):
            idx = model_idx.row()

            del self.pages[idx]
            del self.renders[idx]
            ui.pageScrollArea.takeItem(idx)

            if idx == self.current_page:
                self.show_page(self.current_page - 1)

        self.set_saved(False)

    def rotate_selected(self):
        for model_idx in sorted(list(ui.pageScrollArea.selectedIndexes()), reverse=True):
            idx = model_idx.row()

            result = PageMerge()
            result.add(self.pages[idx], rotate=90)
            new_page = result.render()

            self.pages[idx] = new_page
            self.renders[idx] = self.page_to_img(new_page)

            ui.pageScrollArea.itemWidget(ui.pageScrollArea.item(idx)).set_image(
                self.renders[idx])

            if idx == self.current_page:
                ui.previewArea.load_from_pil(self.renders[idx])

        self.set_saved(False)

    def __init__(self):
        self.reset()
        ui.pageScrollArea.itemClicked.connect(self.handle_item_click)
        ui.actionOpenPages.triggered.connect(lambda: open_pdf())
        ui.previewArea.actionEvent.connect(self.handle_action)

    def reset(self):
        self.current_page = 0
        self.pages = list()
        self.renders = list()
        self.path = None
        self.saved = True
        ui.pageScrollArea.clear()
        self.adjust_title()

    def set_saved(self, saved):
        self.saved = saved
        ui.actionSave.setEnabled(not self.saved)
        self.adjust_title()

    def show_page(self, page_no):

        if page_no < 0:
            page_no = 0
        elif page_no >= len(self.pages):
            page_no = len(self.pages) - 1

        self.current_page = page_no
        ui.previewArea.load_from_pil(self.renders[self.current_page])
        ui.previewArea.pageTextEdit.setText(str(self.current_page + 1))
        ui.pageScrollArea.item(page_no).setSelected(True)
        ui.statusbar.showMessage("Page " + str(page_no + 1) + " / " + str(len(self.pages)))

    def save(self, as_file=None):

        if as_file is not None:
            self.path = as_file

        writer = PdfWriter()
        writer.addpages(self.pages)
        writer.write(self.path)

        self.set_saved(True)
        self.adjust_title()

    def adjust_title(self):
        title = "PyEditPDF"

        if self.path is not None:
            title += " - " + os.path.basename(self.path)

            if not self.saved:
                title += "*"

        MainWindow.setWindowTitle(title)

    def page_to_img(self, page):
        canvas = Canvas("temp.pdf")
        xobj = pagexobj(page)
        canvas.setPageSize((xobj.BBox[2], xobj.BBox[3]))
        canvas.saveState()
        canvas.doForm(makerl(canvas, xobj))
        canvas.restoreState()
        canvas.showPage()
        image = convert_from_bytes(canvas.getpdfdata())[0]
        return image

    def crop_page(self, page, rect):
        page = PageMerge().add(page, viewrect=rect)
        return page.render()

    def adjust_page(self, page, margin=0, scale=1):  # todo: change margin to 4-tuple
        info = PageMerge().add(page)
        x1, y1, x2, y2 = info.xobj_box
        viewrect = (margin, margin, x2 - x1 - 2 * margin, y2 - y1 - 2 * margin) # todo: change margin to 4-tuple
        page = PageMerge().add(page, viewrect=viewrect)
        page[0].scale(scale)
        return page.render()

    def open_pdf(self, file):
        self.reset()
        self.add_pdf(file)
        self.set_saved(True)
        self.show_page(0)

    def add_pdf(self, file):

        if self.path is None:
            self.path = file
            self.adjust_title()

        raw_pages = PdfReader(file).pages
        for page in raw_pages:

            result = PageMerge()
            result.add(page)
            page = result.render()

            self.pages.append(page)
            render = self.page_to_img(page)
            self.renders.append(render)

            new_item = QListWidgetItem()
            ui.pageScrollArea.addItem(new_item)
            page_label = PageLabel(render)
            ui.pageScrollArea.setItemWidget(new_item, page_label)

            page_label.actionEvent.connect(self.handle_action)

        ui.actionSave.setEnabled(True)
        ui.actionSaveAs.setEnabled(True)
        ui.actionAddPages.setEnabled(True)
        ui.actionEditMeta.setEnabled(True)

        self.set_saved(False)


def open_pdf():
    dlg = QFileDialog()
    dlg.setNameFilter("PDF files (*.pdf)")
    if dlg.exec_():
        filenames = dlg.selectedFiles()
        for file in filenames:
            controller.open_pdf(file)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)

    controller = Controller()
    MainWindow.show()
    sys.exit(app.exec_())
