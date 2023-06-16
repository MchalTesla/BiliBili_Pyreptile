import re
import sys
from concurrent.futures import thread

from PyQt5.QtCore import QUrl, QObject, pyqtSignal, Qt, QThread
from PyQt5.QtGui import QPixmap, QIcon, QFont, QTextCursor
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QAction, QListWidget, QLabel, QGridLayout, QDialog, \
    QDialogButtonBox, QLineEdit, QMessageBox, qApp, QPushButton, QSpinBox, QTextEdit, QPlainTextEdit, QTableWidget, \
    QHeaderView, QInputDialog, QTableWidgetItem, QTableView, QSizePolicy, QProgressBar
from fake_useragent import UserAgent

from mysql_concat import mysql_concat
from header import headers
from reptile import ReptileThread
from console import Console




class OutputRedirect(QObject):
    outputWritten = pyqtSignal(str)

    def write(self, text):
        self.outputWritten.emit(str(text))

    def flush(self):
        pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.interval = 1
        self.reptile_thread = None
        self.title = "自适应屏幕大小UI"

        #获取显示器分辨率
        self.desktop = QApplication.desktop()
        self.screenRect = self.desktop.screenGeometry()
        self.screenheight = self.screenRect.height()
        self.screenwidth = self.screenRect.width()

        self.height = int(self.screenheight * 0.7)
        self.width = int(self.screenwidth * 0.7)

        self.resize(self.width,self.height)
        self.wid = QWidget(self)
        self.setCentralWidget(self.wid)
        self.setWindowTitle(self.title)
        self.initUI()
        self.mysqlconcat = None

    def initUI(self):
        self.layout = QGridLayout()
        # 预览四个边都预留20pixs的边界
        self.layout.setContentsMargins(20, 20, 20, 20)
        # 网格之间设置10pixs的间隔
        self.layout.setSpacing(10)

        self.initMenu()
        self.initBrowser()
        self.initToolBar()

        # 创建一个 QLabel 对象，用于显示状态信息
        self.status_label = QLabel("准备就绪，未连接数据库")

        # 创建一个 QProgressBar 对象，用于显示进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)  # 设置最小值
        self.progress_bar.setMaximum(100)  # 设置最大值
        self.progress_bar.setValue(0)  # 设置当前值为 0
        self.statusBar().insertPermanentWidget(1, self.progress_bar, 1)
        self.statusBar().insertPermanentWidget(1, self.status_label, 0)
        # 将 QProgressBar 对象添加到状态栏中
        self.statusBar().addPermanentWidget(self.progress_bar)

        self.wid.setLayout(self.layout)


    def initMenu(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('文件')

        exitAct = QAction('退出', self)
        exitAct.setShortcut('Ctrl+Q')
        # 避免使用已经被占用的文本
        exitAct.setStatusTip('退出程序')
        exitAct.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAct)

        setDBParamsAct = QAction("设置数据库参数", self)
        setDBParamsAct.setStatusTip("设置应用程序使用的数据库参数")
        setDBParamsAct.triggered.connect(self.showDBParamsDialog)

        setWebScrapeParamsAct = QAction("设置爬虫参数", self)
        setWebScrapeParamsAct.setStatusTip("设置应用程序使用的网络爬虫参数")
        setWebScrapeParamsAct.triggered.connect(self.showWebScrapeParamsDialog)

        searchMenu = menubar.addMenu('查询')

        searchNumberAct = QAction('查询视频数量和弹幕数量', self)
        searchNumberAct.setStatusTip('查询视频数量和弹幕数量')
        searchNumberAct.triggered.connect(self.searchNumber)
        searchMenu.addAction(searchNumberAct)

        searchAllVideoAct = QAction('查询所有视频', self)
        searchAllVideoAct.setStatusTip('查询所有视频')
        searchAllVideoAct.triggered.connect(self.searchAllVideo)
        searchMenu.addAction(searchAllVideoAct)

        searchAllDanmuAct = QAction('查询所有弹幕', self)
        searchAllDanmuAct.setStatusTip('查询所有弹幕')
        searchAllDanmuAct.triggered.connect(self.searchAllDanmu)
        searchMenu.addAction(searchAllDanmuAct)

        searchDanmuAct = QAction('查询指定视频的弹幕', self)
        searchDanmuAct.setStatusTip('查询指定视频的弹幕')
        searchDanmuAct.triggered.connect(self.searchDanmu)
        searchMenu.addAction(searchDanmuAct)

        helpMenu = menubar.addMenu('帮助')
        aboutAct = QAction('关于', self)
        aboutAct.setStatusTip('关于此程序')
        aboutAct.triggered.connect(self.showAboutDialog)
        helpMenu.addAction(aboutAct)

        fileMenu.addAction(setDBParamsAct)
        fileMenu.addAction(setWebScrapeParamsAct)

    def showAboutDialog(self):
        QMessageBox.about(self, '关于', '这是由GPT-3.5辅助开发的，基于QT5框架的Bilibili简易爬虫应用。')
    def searchAllVideo(self):
        # 查询并显示所有视频数据
        self.progress_bar.setValue(0)
        if self.mysqlconcat is None or self.mysqlconcat.getstate() == False:
            errorBox = QMessageBox()
            errorBox.setWindowTitle("错误")
            errorBox.setText("连接数据库失败，请检查数据库连接状态。")
            errorBox.setIcon(QMessageBox.Critical)
            errorBox.addButton(QMessageBox.Ok)
            errorBox.exec_()
            return
        cursor = self.mysqlconcat.getdb().cursor()
        cursor.execute("SELECT * FROM video")
        results = cursor.fetchall()
        self.result_table.setColumnCount(6)
        self.result_table.setColumnWidth(0, 100)
        self.result_table.setColumnWidth(1, 150)
        self.result_table.setColumnWidth(2, 120)
        self.result_table.setColumnWidth(3, 450)
        self.result_table.setColumnWidth(4, 750)
        self.result_table.setColumnWidth(5, 100)
        self.result_table.setRowCount(len(results))
        self.status_label.setText("查询到了 "+str(len(results))+" 条数据")
        self.result_table.setHorizontalHeaderLabels(
            ['ID', 'bvid', 'aid', '视频URL', '标题', '弹幕数'])  # 设置标题栏
        for i, row in enumerate(results):
            self.progress_bar.setValue((i+1)*100//len(results))
            for j, item in enumerate(row):
                self.result_table.setItem(i, j, QTableWidgetItem(str(item)))
        self.progress_bar.setValue(100)
        cursor.close()

    def searchAllDanmu(self):
        # 查询并显示所有弹幕数据
        self.progress_bar.setValue(0)
        if self.mysqlconcat is None or self.mysqlconcat.getstate() == False:
            errorBox = QMessageBox()
            errorBox.setWindowTitle("错误")
            errorBox.setText("连接数据库失败，请检查数据库连接状态。")
            errorBox.setIcon(QMessageBox.Critical)
            errorBox.addButton(QMessageBox.Ok)
            errorBox.exec_()
            return
        cursor = self.mysqlconcat.getdb().cursor()
        cursor.execute("SELECT * FROM danmu")
        results = cursor.fetchall()
        self.result_table.setColumnCount(4)
        self.result_table.setColumnWidth(0, 100)
        self.result_table.setColumnWidth(1, 150)
        self.result_table.setColumnWidth(2, 120)
        self.result_table.setColumnWidth(3, 1200)
        self.result_table.setRowCount(len(results))
        self.status_label.setText("查询到了 "+str(len(results))+" 条数据")
        self.result_table.setHorizontalHeaderLabels(['ID', 'bvid', 'cid', '弹幕内容'])  # 设置标题栏
        for i, row in enumerate(results):
            self.progress_bar.setValue((i+1)*100//len(results))
            for j, item in enumerate(row):
                self.result_table.setItem(i, j, QTableWidgetItem(str(item)))
        self.progress_bar.setValue(100)
        cursor.close()
    def searchNumber(self):
        self.progress_bar.setValue(0)
        if self.mysqlconcat is None or self.mysqlconcat.getstate() == False:
            errorBox = QMessageBox()
            errorBox.setWindowTitle("错误")
            errorBox.setText("连接数据库失败，请检查数据库连接状态。")
            errorBox.setIcon(QMessageBox.Critical)
            errorBox.addButton(QMessageBox.Ok)
            errorBox.exec_()
            return
        db = self.mysqlconcat.getdb()
        cursor = db.cursor()
        self.result_table.setColumnCount(2)
        self.result_table.setColumnWidth(0, 500)
        self.result_table.setColumnWidth(1, 500)
        self.result_table.setHorizontalHeaderLabels(['视频数量', '弹幕数量'])
        self.result_table.setRowCount(1)
        sql = "SELECT (SELECT COUNT(*) from video), (SELECT COUNT(*) FROM danmu)"
        cursor.execute(sql)
        dump = cursor.fetchone()
        cursor.close()
        self.result_table.setItem(0, 0, QTableWidgetItem(str(dump[0])))
        self.result_table.setItem(0, 1, QTableWidgetItem(str(dump[1])))
        self.progress_bar.setValue(100)
    def searchDanmu(self):
        # 弹出输入框，让用户输入 bvid 或者 title，查询指定视频的弹幕数据
        self.progress_bar.setValue(0)
        text, ok = QInputDialog.getText(self, '指定视频弹幕查询', '请输入bvid或者title:')
        if ok:
            keyword = str(text).strip()
            if self.mysqlconcat is None or self.mysqlconcat.getstate() == False:
                errorBox = QMessageBox()
                errorBox.setWindowTitle("错误")
                errorBox.setText("连接数据库失败，请检查数据库连接状态。")
                errorBox.setIcon(QMessageBox.Critical)
                errorBox.addButton(QMessageBox.Ok)
                errorBox.exec_()
                return
            db = self.mysqlconcat.getdb()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM danmu WHERE bvid=%s OR bvid=(SELECT bvid FROM video WHERE title LIKE %s)", (keyword, '%' + keyword + '%',))
            results = cursor.fetchall()
            self.result_table.setColumnCount(4)
            self.result_table.setColumnWidth(0, 100)
            self.result_table.setColumnWidth(1, 150)
            self.result_table.setColumnWidth(2, 120)
            self.result_table.setColumnWidth(3, 1200)
            self.result_table.setRowCount(len(results))
            self.status_label.setText("查询到了 " + str(len(results)) + " 条数据")
            self.result_table.setHorizontalHeaderLabels(['ID', 'bvid', 'cid', '弹幕内容'])  # 设置标题栏
            for i, row in enumerate(results):
                self.progress_bar.setValue((i + 1) * 100 // len(results))
                for j, item in enumerate(row):
                    self.result_table.setItem(i, j, QTableWidgetItem(str(item)))
            self.progress_bar.setValue(100)
            cursor.close()
    def initToolBar(self):
        # 创建工具栏
        toolbar = self.addToolBar('爬取')

        # 创建搜索框
        search_box = QLineEdit(self)
        search_box.setPlaceholderText('输入关键字爬取')
        search_box.setMaximumHeight(40)
        search_box.setMinimumHeight(40)
        search_box.setFont(QFont("Arial", 12))  # 设置字体大小为12
        toolbar.addWidget(search_box)

        # 创建页数选择框
        page_spinbox = QSpinBox(self)
        page_spinbox.setMinimum(1)
        page_spinbox.setMaximum(100)
        page_spinbox.setValue(1)
        page_spinbox.setMaximumHeight(40)
        page_spinbox.setMinimumHeight(40)
        page_spinbox.setFont(QFont("Arial", 12))
        toolbar.addWidget(page_spinbox)

        # 创建爬取按钮
        search_btn = QAction(QIcon('reptile.png'), '爬取', self)
        search_btn.triggered.connect(lambda: self.search(search_box.text(), int(page_spinbox.text())))
        toolbar.addAction(search_btn)

    def search(self, keyword, number):
        # 执行搜索操作
        self.progress_bar.setValue(0)
        if self.reptile_thread and self.reptile_thread.isRunning():
            self.reptile_thread.stop()
            return

        if len(keyword) == 0:
            errorBox = QMessageBox()
            errorBox.setWindowTitle("错误")
            errorBox.setText("爬取关键字长度为 0")
            errorBox.setIcon(QMessageBox.Critical)
            errorBox.addButton(QMessageBox.Ok)
            errorBox.exec_()
            return
        if self.mysqlconcat is None or self.mysqlconcat.getstate() == False:
            errorBox = QMessageBox()
            errorBox.setWindowTitle("错误")
            errorBox.setText("连接数据库失败，请检查数据库连接状态。")
            errorBox.setIcon(QMessageBox.Critical)
            errorBox.addButton(QMessageBox.Ok)
            errorBox.exec_()
            return
        self.status_label.setText("正在爬取")
        db = self.mysqlconcat.getdb()
        self.reptile_thread = ReptileThread(db, keyword, number, self.interval)
        self.reptile_thread.progress.connect(self.update_progress)
        self.reptile_thread.finished.connect(self.display_result)
        self.reptile_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def display_result(self):
        videocount = self.reptile_thread.videocount
        danmucount = self.reptile_thread.danmucount
        self.status_label.setText("准备就绪，已连接到数据库")
        print("共爬取了 {0} 个视频, {1} 个弹幕".format(videocount, danmucount))
        if videocount == 0:
            print("尝试换一个User-Agent试试")


    def initBrowser(self):
        # 创建数据库管理界面
        self.result_table = QTableWidget(self)
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(['视频数量', '弹幕数量'])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.result_table.setColumnWidth(0, 500)
        self.result_table.setColumnWidth(1, 500)
        self.result_table.setRowCount(1)
        self.result_table.setItem(0, 0, QTableWidgetItem('请连接数据库'))
        self.layout.addWidget(self.result_table, 0, 0, 1, 2)

        # 创建输出窗口
        self.console = QPlainTextEdit(self)
        # self.console.moveCursor(QTextCursor.End)
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(200)
        self.layout.addWidget(self.console, 1, 0, 1, 2)
        self.outputRedirect = OutputRedirect(self)
        self.outputRedirect.outputWritten.connect(self.console.insertPlainText)
        sys.stdout = self.outputRedirect
        sys.stderr = self.outputRedirect
        self.thread = Console(self)
        self.thread.start()
        self.console.installEventFilter(self)

    def eventFilter(self, obj, event):
        # 捕获消息框的 enterEvent 和 leaveEvent 事件
        if obj == self.console and (event.type() == event.Enter or event.type() == event.Leave):
            if event.type() == event.Enter:
                # 鼠标进入消息框，暂停线程
                self.thread.pause()
            else:
                # 鼠标离开消息框，恢复线程
                self.thread.resume()

        # 将事件传递给父类处理
        return super().eventFilter(obj, event)


    def showDBParamsDialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("设置数据库参数")
        dialog.setModal(True)
        dialog.setMinimumWidth(250)

        # Create line edits for each parameter
        hostEdit = QLineEdit(dialog)
        portEdit = QLineEdit(dialog)
        usernameEdit = QLineEdit(dialog)
        passwordEdit = QLineEdit(dialog)
        databaseEdit = QLineEdit(dialog)

        # Set default values for the line edits
        hostEdit.setText("localhost")
        portEdit.setText("3306")
        usernameEdit.setText("bilibili")
        databaseEdit.setText("bilibili")
        passwordEdit.setEchoMode(QLineEdit.Password)

        # Add labels and line edits to the form layout
        layout = QGridLayout()
        layout.addWidget(QLabel("Host:"), 0, 0)
        layout.addWidget(hostEdit, 0, 1)
        layout.addWidget(QLabel("Port:"), 1, 0)
        layout.addWidget(portEdit, 1, 1)
        layout.addWidget(QLabel("Username:"), 2, 0)
        layout.addWidget(usernameEdit, 2, 1)
        layout.addWidget(QLabel("Password:"), 3, 0)
        layout.addWidget(passwordEdit, 3, 1)
        layout.addWidget(QLabel("Database:"), 4, 0)
        layout.addWidget(databaseEdit, 4, 1)

        # Add OK and Cancel buttons to the dialog box
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        layout.addWidget(buttonBox, 5, 0, 1, 2)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            host = hostEdit.text()
            port = portEdit.text()
            username = usernameEdit.text()
            password = passwordEdit.text()
            database = databaseEdit.text()

            self.mysqlconcat = mysql_concat(host=host, port=port, user=username, password=password, database=database)
            if self.mysqlconcat.getstate():
                self.status_label.setText("准备就绪，已连接到数据库")
                sql = "SELECT (SELECT COUNT(*) from video), (SELECT COUNT(*) FROM danmu)"
                cursor = self.mysqlconcat.getdb().cursor()
                cursor.execute(sql)
                dump = cursor.fetchone()
                cursor.close()
                self.result_table.setItem(0, 0, QTableWidgetItem(str(dump[0])))
                self.result_table.setItem(0, 1, QTableWidgetItem(str(dump[1])))
            else:
                errorBox = QMessageBox()
                errorBox.setWindowTitle("错误")
                errorBox.setText("连接数据库失败，请检查参数后重试。")
                errorBox.setIcon(QMessageBox.Critical)
                errorBox.addButton(QMessageBox.Ok)
                errorBox.exec_()
                self.status_label.setText("未连接到数据库")

    def showWebScrapeParamsDialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("设置爬虫参数")
        dialog.setModal(True)
        dialog.setMinimumWidth(250)

        # Create line edits for each parameter
        referEdit = QLineEdit("https://www.google.com/", dialog)
        cookieEdit = QLineEdit(dialog)
        userAgentEdit = QLineEdit("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36", dialog)
        intervalEdit = QLineEdit(str(self.interval), dialog)

        # Add labels and line edits to the form layout
        layout = QGridLayout()
        layout.addWidget(QLabel("Refer:"), 0, 0)
        layout.addWidget(referEdit, 0, 1)
        layout.addWidget(QLabel("Cookie:"), 1, 0)
        layout.addWidget(cookieEdit, 1, 1)
        layout.addWidget(QLabel("User-Agent:"), 2, 0)
        layout.addWidget(userAgentEdit, 2, 1)
        layout.addWidget(QLabel("爬虫间隔时间(s):"), 3, 0)
        layout.addWidget(intervalEdit, 3, 1)

        # Add random user agent button to the form layout
        randUserAgentButton = QPushButton("随机 User-Agent", dialog)
        randUserAgentButton.clicked.connect(lambda: userAgentEdit.setText(UserAgent().random))
        layout.addWidget(randUserAgentButton, 2, 2)

        # Add OK and Cancel buttons to the dialog box
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        layout.addWidget(buttonBox, 4, 0, 1, 2)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            headers['User-Agent'] = userAgentEdit.text()
            headers['Referer'] = referEdit.text()
            headers['Cookie'] = cookieEdit.text()
            self.interval = int(intervalEdit.text())


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
