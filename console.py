from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor


class Console(QThread):
    tick = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.count = 0
        self.paused = False

    def run(self):
        while True:
            if not self.paused:
                self.tick.emit(self.count)
                self.count += 1
                # 将光标移动到文本框结尾
                cursor = self.parent().console.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.parent().console.setTextCursor(cursor)
            self.msleep(1)  # 暂停 1 毫秒

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False