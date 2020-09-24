import mysql.connector as connector
import logging

# ....
SAVE_ON_DISCONNECT = True

# Logging
logging.basicConfig(filename='database.log', format='%(asctime)s - Process ID:%(process)d ---- %(levelname)s ---- %(message)s', datefmt='%d-%b-%y %H:%M:%S')

class mysqlDB():
    def __init__(self, MYSQL_HOST, MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DATABASE):
        self.host = MYSQL_HOST
        self.username = MYSQL_USERNAME
        self._password = MYSQL_PASSWORD
        self.database = MYSQL_DATABASE
        
        self.connection = self.connectDB()
        self.cursor = self.getNewCursor() if self.getConnection() else False
        
    def save(self):
        self.connection.commit()
    
    def rollback(self):
        self.connection.rollback()
        
    def getConnection(self):
        return self.connection
    
    def getCursor(self):
        return self.cursor
    
    def connectDB(self):
        try:
            self.connection = connector.connect(host = self.host, user = self.username, passwd = self._password, database = self.database)
            print("\n-------Connection to MySQL DB successful-------\n")
            logging.debug(f'Connection to Database: {self.database} was successful')
        except connector.Error as e:
            print(f"The error '{e}' occurred")
            logging.error(f'Connection to Database: {self.database} was unsuccessful')
            return False
        return self.connection

    def disconnectDB(self, save=1):
        if self.getConnection():
            # save
            if save:
                self.save()

            # disconnect
            self.cursor.close()
            self.connection.close()
            # logging.debug('Connection to database has been stopped')

    def getNewCursor(self):
        try:
            self.connection.ping(reconnect=True, attempts=3, delay=5)
        except connector.Error:
            logging.debug(f'Connection to Database: {self.database} was unsuccessful')
            self.connection = self.connectDB()
        return self.connection.cursor(buffered=True) if self.connection else False