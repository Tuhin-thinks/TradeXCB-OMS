from PyQt5 import QtWidgets, QtCore, QtGui
from Libs.Utils import settings


class ImageViewer(QtWidgets.QLabel):
    """custom label to maintain the aspect ratio of it's image pixmap"""

    def __init__(self, pixmap):
        super(ImageViewer, self).__init__()
        self._image_pixmap: 'QtGui.QPixmap' = pixmap
        self._max_size = settings.MIN_HEIGHT

    def update_pixmap(self, pixmap):
        """update label's pixmap by resizing the original pixmap"""
        self._image_pixmap = pixmap
        self.set_scaled_pixmap()

    def set_scaled_pixmap(self):
        if self._image_pixmap:
            pixmap = self._image_pixmap.scaledToHeight(self._max_size-80, QtCore.Qt.SmoothTransformation)
            self.setPixmap(pixmap)
            self.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignCenter)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super(ImageViewer, self).resizeEvent(event)
        self.set_scaled_pixmap()
