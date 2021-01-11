import mysql.connector as connector
import logging

# Save when disconnected from database server
SAVE_ON_DISCONNECT = True

# Logging
logging.basicConfig(filename='database.log', format='%(asctime)s - Process ID:%(process)d ---- %(levelname)s ---- %(message)s', datefmt='%d-%b-%y %H:%M:%S')

class mysqlDB():
    def __init__(self, MYSQL_HOST, MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DATABASE):
        self.host = MYSQL_HOST
        self.username = MYSQL_USERNAME
        self._password = MYSQL_PASSWORD
        self.database = MYSQL_DATABASE
        self.connection = 0
        self.connectDB()
        self.cursor = self.getNewCursor() if self.getConnection().is_connected() else False
        
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
            connection = connector.connect(host = self.host, user = self.username, passwd = self._password, database = self.database)
            logging.debug(f'Connection to Database: {self.database} was successful')
        except:
            logging.error(f'Connection to Database: {self.database} was unsuccessful')
        self.connection = connection

    def disconnectDB(self, save=1):
        if self.getConnection() is not False:
            # save
            if save: self.save()

            # disconnect
            self.cursor.close()
            self.connection.close()
            self.connection = False
            # logging.debug('Connection to database has been stopped')

    def getNewCursor(self):
        try:
            self.connection.ping(reconnect=True, attempts=3, delay=4)
        except connector.Error:
            logging.debug(f'Connection to Database: {self.database} was unsuccessful')
            self.connection = self.connectDB()
        return self.connection.cursor(buffered=True)