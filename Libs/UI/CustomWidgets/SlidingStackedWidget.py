import random
from PyQt5 import QtCore, QtGui, QtWidgets


class SlidingStackedWidget(QtWidgets.QStackedWidget):
    def __init__(self, parent=None):
        super(SlidingStackedWidget, self).__init__(parent)

        self.m_direction = QtCore.Qt.Horizontal
        self.m_speed = 250
        self.m_animationType = QtCore.QEasingCurve.InCurve
        self.m_now = 0
        self.m_next = 0
        self.m_wrap = False
        self.m_pnow = QtCore.QPoint(0, 0)
        self.m_active = False

    def setDirection(self, direction):
        self.m_direction = direction

    def setSpeed(self, speed):
        self.m_speed = speed

    def setAnimation(self, animation_type):
        self.m_animationType = animation_type

    def setWrap(self, wrap):
        self.m_wrap = wrap

    @QtCore.pyqtSlot()
    def slideInPrev(self):
        now = self.currentIndex()
        if self.m_wrap or now > 0:
            self.slideInIdx(now - 1)

    @QtCore.pyqtSlot()
    def slideInNext(self):
        now = self.currentIndex()
        if self.m_wrap or now < (self.count() - 1):
            self.slideInIdx(now + 1)

    def slideInIdx(self, idx):
        if idx > (self.count() - 1):
            idx = idx % self.count()
        elif idx < 0:
            idx = (idx + self.count()) % self.count()
        self.slideInWgt(self.widget(idx))

    def slideInWgt(self, new_widget):
        if self.m_active:
            return

        self.m_active = True

        _now = self.currentIndex()
        _next = self.indexOf(new_widget)

        if _now == _next:
            self.m_active = False
            return

        offset_X, offset_Y = self.frameRect().width(), self.frameRect().height()
        self.widget(_next).setGeometry(self.frameRect())

        if not self.m_direction == QtCore.Qt.Horizontal:
            if _now < _next:
                offset_X, offset_Y = 0, -offset_Y
            else:
                offset_X = 0
        else:
            if _now < _next:
                offset_X, offset_Y = -offset_X, 0
            else:
                offset_Y = 0

        page_next = self.widget(_next).pos()
        pnow = self.widget(_now).pos()
        self.m_pnow = pnow

        offset = QtCore.QPoint(offset_X, offset_Y)
        self.widget(_next).move(page_next - offset)
        self.widget(_next).show()
        self.widget(_next).raise_()

        anim_group = QtCore.QParallelAnimationGroup(self)
        anim_group.finished.connect(self.animationDoneSlot)

        for index, start, end in zip(
            (_now, _next), (pnow, page_next - offset), (pnow + offset, page_next)
        ):
            animation = QtCore.QPropertyAnimation(self.widget(index), b'pos')
            animation.setEasingCurve(self.m_animationType)
            animation.setDuration(self.m_speed)
            animation.setStartValue(start)
            animation.setEndValue(end)
            anim_group.addAnimation(animation)

        self.m_next = _next
        self.m_now = _now
        self.m_active = True
        anim_group.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    @QtCore.pyqtSlot()
    def animationDoneSlot(self):
        self.setCurrentIndex(self.m_next)
        self.widget(self.m_now).hide()
        self.widget(self.m_now).move(self.m_pnow)
        self.m_active = False


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        slidingStacked = SlidingStackedWidget()
        for i in range(10):
            label = QtWidgets.QLabel(
                "Qt is cool " + i * "!", alignment=QtCore.Qt.AlignCenter
            )
            color = QtGui.QColor(*random.sample(range(255), 3))
            label.setStyleSheet(
                "QLabel{ background-color: %s; color : white; font: 40pt}"
                % (color.name(),)
            )
            slidingStacked.addWidget(label)

        button_prev = QtWidgets.QPushButton(
            "Previous", pressed=slidingStacked.slideInPrev
        )
        button_next = QtWidgets.QPushButton(
            "Next", pressed=slidingStacked.slideInNext
        )

        hlay = QtWidgets.QHBoxLayout()
        hlay.addWidget(button_prev)
        hlay.addWidget(button_next)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        lay = QtWidgets.QVBoxLayout(central_widget)
        lay.addLayout(hlay)
        lay.addWidget(slidingStacked)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.resize(640, 480)
    w.show()
    sys.exit(app.exec_())
