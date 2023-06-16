import pymysql

class mysql_concat:
    _host = 'localhost'
    _port = 3306
    _user = None
    _password = None
    _database = None
    _db = None
    _state = False

    def __init__(self, host, port, user, password, database):
        self._host = host
        self._user = user
        self._port = port
        self._password = password
        self._database = database
        try:
            self._db = pymysql.connect(host=self._host, port=int(self._port), user=self._user, password=self._password, database=self._database)
            cursor = self._db.cursor()
            cursor.execute("SHOW TABLES")
            result = cursor.fetchall()

            if ('video',) not in result:
                cursor.execute("CREATE TABLE video (id INT AUTO_INCREMENT PRIMARY KEY, bvid VARCHAR(16), aid VARCHAR(16), "
                               "videourl VARCHAR(100), title VARCHAR(100), numberofvideo INT, numberofdanmu INT)")

            if ('danmu',) not in result:
                cursor.execute("CREATE TABLE danmu (id INT AUTO_INCREMENT PRIMARY KEY, bvid VARCHAR(16), cid VARCHAR(16), "
                               "danmu VARCHAR(255))")

            self._state = True
            cursor.close()
        except Exception as e:
            print(f"Failed to connect to the database: {e}")
            self._state = False

    def __del__(self):
        if(self._state):
            self._db.close()

    def getstate(self):
        return self._state

    def getdb(self):
        return self._db