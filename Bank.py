import MySQLConnector
import time
import configparser
import logging
import tabulate

# Defaults
DEFAULT_PAGE_WIDTH = 60
DEFAULT_ACCOUNT_NAME = "John Doe"
DEFAULT_BALANCE = 0

# Debugger
DEBUG = 0
VERBOSE_MAIN_FUNCTIONS = 0

# Logging
logging.basicConfig(filename='bank.log', format='%(asctime)s - Process ID: %(process)d ---- %(levelname)s ---- %(message)s', datefmt='%d-%b-%y %H:%M:%S')

# Status of request
STATUS_START = 1
STATUS_LOAD  = 2
STATUS_COMP  = 3
STATUS_EXIT  = 4
STATUS_ERROR = 0

# State of session
STATE_LOGGED_IN  = 1
STATE_LOGGED_OUT = 0

# Credentials File
CRED_FILE = "config.ini"
config = configparser.ConfigParser()
config.read(CRED_FILE)

# Credentials
MYSQL_HOST     = config["MYSQL"]["host"]
MYSQL_USERNAME = config["MYSQL"]["username"]
MYSQL_PASSWORD = config["MYSQL"]["password"]
MYSQL_DATABASE = config["MYSQL"]["database"]


########## Useful functions for displaying and retrieving input #############

# printStrings
## Print messsages/string with dotted lines on each side 
##      with a corresponding prefix, suffix, and length
def printString(string="", prefix="\n", suffix="\n", length=50):
    left_ext = right_ext = 0
    
    if length > len(string)+1 and string:
        left_ext = right_ext = (length - len(string)) // 2
        # if length % 2: left_ext += 1
    print(f'{prefix}{left_ext*"-"}{string}{right_ext*"-"}{suffix}')

# printStatus
## Print the current status of the main Bank functions running if DEBUG is set to 1 or True
def printStatus(code, v=1):
    if v:
        if   code == 1: printString("Starting...", length=0)
        elif code == 2: printString("Loading...", length=0)
        elif code == 3: printString("Complete.", length=0)
        elif code == 4: printString("Exiting.", length=0)
        else:           printString("ERROR.", length=0)

# getInput
## Retrieve input based on desired type with a prefix and separator field
def getInput(inputType=int, prefix="", sep=": ", v=True):
    output = None
    while True:
        try:
            output = inputType(input(f"{prefix}{sep}"))
            break
        except (ValueError, TypeError):
            if v: printString("Please try again.", prefix="", length=0)
        except: pass
    return output


########### Main queries to be sent to the MySQL server for execution ############


# selectRowByAccNbr
## Retreives account information based on account number
def selectRowByAccNbr(dbObj, acc_no, lock=False):
    query = "SELECT * FROM accounts WHERE account_no = %s"
    query += " FOR UPDATE;" if lock else ";"
    dbObj.getCursor().execute(query, (int(acc_no),))

# updateBalanceByAccNbr
## Updates balance based on account number
def updateBalanceByAccNbr(dbObj, acc_no, balance): dbObj.getCursor().execute("UPDATE accounts SET balance=%s WHERE account_no=%s;", (int(balance), int(acc_no)))

# addAccount
## Adds a new account/entry into the accounts table with a name and starting balance as input
def addAccount(dbObj, name, balance): dbObj.getCursor().execute("INSERT INTO accounts (name, balance) VALUES (%s, %s);", (name, int(balance)))

# getBalance
## Retreives balance based on account number
def getBalance(dbObj, acc_no): dbObj.getCursor().execute("SELECT balance FROM accounts WHERE account_no = %s;", (int(acc_no),))

# startTransaction
## Begins database transation
## saveTransaction must be run at the end of the transaction
def startTransaction(dbObj): dbObj.getCursor().execute("START TRANSACTION;", ())
 
# saveTransaction
## Commits/saves transaction to database
## startTransaction NOT required to be run before this function
def saveTransaction(dbObj): dbObj.save()

# rollbackTransaction
## Clears the current transaction
## startTransaction IS required to be run before this function
def rollbackTransaction(dbObj): dbObj.rollback()



########## Bank Class ##########

# Bank - class
### Provides necessary functions for a Bank to run
### Provides middle man servcies to the database and User Interface
##    __init__                        
##    getAccountInfo     ## Static method - Retrieves account information
##    createAccount      ## Creates an entry in database for the client where their banking information is stored
##    checkBalance       ## Retrieve current balance
##    changeBalanceMain  ## Perform arithmetic operations on balance
##    changeBalance      ## Change balance of account based on action (desposit and withdraw)
##    deposit            ## Desposit money to account based on account number
##    withdraw           ## Withdraw money from account based on account number
##    transfer           ## Transfer money from source to target account
class Bank():
    
    # __init__
    ### Create instance variable to hold MySQL database connection details
    def __init__(self, databaseObject):
        self.dbObj = databaseObject
    
    ########### Execute an import MySQL query with error handlers ############
    
    @staticmethod
    def getAccountInfo(dbObj, acc_no, balanceOnly=False, v=0, lock=False):
        # getAccountInfo - static method
        ## try: Obtain account information via database table
        ## except: log database error and raise error
        ## else: check if any data was recieved
        ##    if no data recieved raise exception
        ##    else there is data
        ##         return the appropriate data
        try:
            selectRowByAccNbr(dbObj, acc_no, lock)
        except Exception as e:
            printString("Database Error", length=DEFAULT_PAGE_WIDTH)
            logging.error(e)
            raise Exception()
        else:
            row = dbObj.getCursor().fetchone()
            if row is None:
                logging.error(f"The account, with id = {acc_no}, does not exist")
                raise ValueError("Account does not exist", acc_no)
            
            # row[1] = name
            # row[2] = balance
            # row[3] = open date
            if v:
                print(f"Name:           {row[1]}\n"
                    + f"Balance:        {row[2]}\n"
                    + f"Opening Date:   {row[3]}\n")
                
            logging.debug(f"Fetching account {acc_no} was successful")
            
            if balanceOnly: return row[2]
            return row[1:]
        
    def createAccount(self, name=DEFAULT_ACCOUNT_NAME, balance=DEFAULT_BALANCE, v=VERBOSE_MAIN_FUNCTIONS):
        # createAccount
        ## start SQL transction
        ## add the account
        ## commit the changes to the database
        ## if there is an error
        ##     rollback transaction and log error
        printStatus(STATUS_LOAD, DEBUG)
        
        if v:
            print("Create Account")
            print(f"acc_name: {name}")
            print(f"balance: {balance}")
        
        try:
            startTransaction(self.dbObj)
            addAccount(self.dbObj, name, balance)
            saveTransaction(self.dbObj)
            
            printStatus(STATUS_COMP, DEBUG)
            logging.debug(f"Account creation for '{name}' was successful")
            return True
        except Exception as e:
            rollbackTransaction(self.dbObj)
            logging.error(e)
        
        printStatus(STATUS_ERROR, DEBUG)
        return False
    
    def checkBalance(self, acc_no, v=VERBOSE_MAIN_FUNCTIONS):
        # checkBalance
        ## Run getAccountInfo to retrieve account information from database
        ## if there is an error
        ##      log error
        printStatus(STATUS_LOAD, DEBUG)
        
        if v:
            print("Check Balance")
            print(f"acc_no: {acc_no}")
            
        try:
            balance = __class__.getAccountInfo(self.dbObj, acc_no, balanceOnly=True)
            printStatus(STATUS_COMP, DEBUG)
            
            logging.debug(f"Checking balance for (Account Id: {acc_no}) was successful")
            return balance
        except Exception as e:
            logging.error(e)
            
        printStatus(STATUS_ERROR, DEBUG)
        return False

    def changeBalanceMain(self, acc_no, balance, amount, action, v=VERBOSE_MAIN_FUNCTIONS):
        # changeBalanceMain
        ## Lock row based on account number
        ## Perform operation based on action
        ## Update balance for the associated account
        selectRowByAccNbr(self.dbObj, acc_no)
        
        if action == 'deposit': balance += amount
        elif action == 'withdraw': balance -= amount
        else: return balance
        
        updateBalanceByAccNbr(self.dbObj, acc_no, balance)
        return balance
    
    def changeBalance(self, acc_no, amount, action, v=VERBOSE_MAIN_FUNCTIONS):
        # changeBalance
        ## Check if amount is a valid input
        ## Retrieve account information
        ## start SQL transction
        ## Perform arithmetic operations on balance
        ## Commit/save transaction to database
        ## if there is an error
        ##     rollback transactions
        printStatus(STATUS_LOAD, DEBUG)
        
        if v: 
            print(f"{action}")
            print(f"acc_no: {acc_no}")
            print(f"amount: {amount}")
        
        try:
            assert(amount > 0)
            
            startTransaction(self.dbObj)
            balance = __class__.getAccountInfo(self.dbObj, acc_no, balanceOnly=True, lock=True)
            balance = self.changeBalanceMain(acc_no, balance, amount, action)
            saveTransaction(self.dbObj)
            
            printStatus(STATUS_COMP, DEBUG)
            logging.debug(f"{action} (Account Id: {acc_no}) was successful")
            
            return balance
        except Exception as e:
            rollbackTransaction(self.dbObj)
            logging.error(e)
        
        # Deposit failure
        printStatus(STATUS_ERROR, DEBUG)
        return False
    
    def deposit(self, acc_no, deposit_amount, v=VERBOSE_MAIN_FUNCTIONS):
        # Deposit
        ## Run changeBalance on account
        return self.changeBalance(acc_no, deposit_amount, 'deposit')

    def withdraw(self, acc_no, withdraw_amount, v=VERBOSE_MAIN_FUNCTIONS):
        # Withdraw
        ## Run changeBalance on account
        return self.changeBalance(acc_no, withdraw_amount, action='withdraw')

    def transfer(self, src_acc_no, trgt_acc_no, transfer_amount, v=VERBOSE_MAIN_FUNCTIONS):
        # Transfer
        ## Check if amount is a valid input
        ## Begin SQL transction
        ## Retrieve account information for source and target account
        ## Perform arithmetic operations on balance
        ## Commit/save transaction to database
        ## if there is an error
        ##     rollback transactions
        printStatus(STATUS_LOAD, DEBUG)
        
        if v:
            print("transfer")
            print(f"source_acc_no: {src_acc_no}")
            print(f"target_acc_no: {trgt_acc_no}")
            print(f"deposit_amount: {transfer_amount}")
        
        switch = 0
        try:
            assert(transfer_amount > 0)
            
            startTransaction(self.dbObj)
            src_name, src_balance, src_open_date = __class__.getAccountInfo(self.dbObj, src_acc_no, lock=True)
            switch += 1
            trgt_name, trgt_balance, trgt_open_date = __class__.getAccountInfo(self.dbObj, trgt_acc_no, lock=True)
            switch += 1
            
            src_balance  = self.changeBalanceMain(src_acc_no, src_balance, transfer_amount, 'withdraw')
            trgt_balance = self.changeBalanceMain(trgt_acc_no, trgt_balance, transfer_amount, 'deposit')
            saveTransaction(self.dbObj)

            printStatus(STATUS_COMP, DEBUG)
            logging.debug(f"transfer from (Account Id: {src_acc_no}) to (Account Id: {trgt_acc_no}) was successful")
            
            return (src_name, trgt_name, src_balance, trgt_balance)
        except Exception as e:
            rollbackTransaction(self.dbObj)
            logging.error(e)
        
        # Transfer failure
        printStatus(STATUS_ERROR, DEBUG)
        
        return (False, switch)

    
########## Connect to the Bank via a Session rather than directly (like an ATM) #############

# BankSession - class
### Provides a User Interface to the Bank
##    __init__                  ## Inherit and add database connection object to the Bank superclass and create session variables
##    clearSessionVariables     ## Reset/Create session variables
##    getAccountInfo            ## Obtain Account Information for the associated account
##    getAccountNumber          ## Same functionality as getInput, but provides a pre-defined prefix and a unquie func name for readability
##    printAccountInfo          ## Utilize tabulate module to create a table with the appropriate data
##    displayOptions            ## ## Display available functions the Bank has to offer to the customer
##    selectOptions             ## Run appropriate functions based on user input
##    createAccount             ## Create a Bank Account
##    checkBalance              ## Check balance of existing an account
##    deposit                   ## Deposit to an existing account
##    withdraw                  ## Withdraw from an existing account
##    transfer                  ## Transfer from a source account to a target account
class BankSession(Bank):
    
    def __init__(self, databaseObject):
        # __init__
        ## inherit and add database connection object to the Bank superclass
        ## Create session variables
        
        super().__init__(databaseObject)
        self.clearSessionVariables()
    
    def clearSessionVariables(self):
        # clearSessionVariables
        self.id = self.state = STATE_LOGGED_OUT
        self.name = self.open_date = ''
    
    def getAccountInfo(self):
        # getAccountInfo
        ## Must get account information if client is NOT logged in
        ## loop
        ##     First obtain an account number
        ##     if account does not exist (in database)
        ##          repeat loop and reset session variables
        ##     else
        ##          set session variables to the information that was obtained (from database)
    
        while self.state != STATE_LOGGED_IN:
            self.id = self.getAccountNumber()
            try:
                self.name, balance, self.open_date = Bank.getAccountInfo(self.dbObj, self.id)
                self.state = STATE_LOGGED_IN
            except ValueError:
                print("Account does not exist. Please try again.\n")
                self.clearSessionVariables()
            except:
                self.clearSessionVariables()
                
    def getAccountNumber(self, string="Account Number"):
        # getAccountNumber
        return getInput(inputType=int, prefix=string, sep=": ")

    def printAccountInfo(self, IDs=[], names=[], balances=[], open_dates=[]):
        # printAccountInfo
        print(f'\n{tabulate.tabulate({"ID": IDs, "Name": names, "Balance": balances, "Open Date": open_dates}, headers="keys")}')

    def displayOptions(self):
        # displayOptions
        ## Display available functions the Bank has to offer
        printString("Main Menu", length=DEFAULT_PAGE_WIDTH)
        
        if self.state == STATE_LOGGED_IN: print(f"Account logged in: {self.id}\n")
        print("1 - Create an Account\n"
            + "2 - Check Balance\n"
            + "3 - Desposit\n"
            + "4 - Withdraw\n"
            + "5 - Transfer\n"
            + "9 - Log out\n"
            + "0 - Log out and Exit\n")

    def selectOption(self, code):
        # selectOption
        printStatus(STATUS_START, DEBUG)
        
        # Create Account
        if code == 1:
            self.clearSessionVariables()
            acc_name = getInput(str, "Enter an Account Name")
            balance = getInput(prefix="Enter initial balance")
            self.createAccount(acc_name, balance)
            
        elif 1 < code < 6:
            # Get account information if not logged in
            if self.state != STATE_LOGGED_IN: self.getAccountInfo()
                
            # Check Balance
            if code == 2: self.checkBalance()
            
            # Deposit
            elif code == 3:
                deposit_amount = getInput(prefix="Deposit Amount")
                self.deposit(deposit_amount)
                
            # Withdraw
            elif code == 4:
                withdraw_amount = getInput(prefix="Withdraw Amount")
                self.withdraw(withdraw_amount)
            
            # Transfer
            elif code == 5:
                trgt_acc_no = self.getAccountNumber("Target Account Number")
                transfer_amount = getInput(prefix="Transfer Amount")
                self.transfer(trgt_acc_no, transfer_amount)
        # Log out       
        elif code == 9: self.clearSessionVariables()
            
        # Disconnect
        elif code == 0:
            self.dbObj.disconnectDB(MySQLConnector.SAVE_ON_DISCONNECT)
            return False
            
        # Invalid code - print error message
        else: printString("Invalid code - Please try again", length=DEFAULT_PAGE_WIDTH)
        
    def createAccount(self, name=DEFAULT_ACCOUNT_NAME, balance=DEFAULT_BALANCE, v=VERBOSE_MAIN_FUNCTIONS):
        # createAccount
        ## Run superclass version of createAccount
        ## Display appropriate result
        
        if super().createAccount(name, balance, v): printString("Account successfully created", length=DEFAULT_PAGE_WIDTH)
        else: printString("Account creation unsuccessful", length=DEFAULT_PAGE_WIDTH)
        
    def checkBalance(self, v=VERBOSE_MAIN_FUNCTIONS):
        # checkBalance
        ## Run superclass version of checkBalance
        ## Display appropriate result
        
        balance = super().checkBalance(self.id, v)
        if balance is not False: self.printAccountInfo([self.id], [self.name], [balance], [self.open_date])
        else: printString("Check Balance unsuccessful", length=DEFAULT_PAGE_WIDTH)
    
    def deposit(self, deposit_amount, v=VERBOSE_MAIN_FUNCTIONS):
        # deposit
        ## Run superclass version of deposit
        ## Display appropriate result
        
        balance = super().deposit(self.id, deposit_amount, v)
        if balance is not False: self.printAccountInfo([self.id], [self.name], [balance], [self.open_date])
        else: printString("Deposit unsuccessful", length=DEFAULT_PAGE_WIDTH)
    
    def withdraw(self, withdraw_amount, v=VERBOSE_MAIN_FUNCTIONS):
        # withdraw
        ## Run superclass version of withdraw
        ## Display appropriate result
        
        balance = super().withdraw(self.id, withdraw_amount, v)
        if balance is not False: self.printAccountInfo([self.id], [self.name], [balance], [self.open_date])
        else: printString("Withdraw unsuccessful", length=DEFAULT_PAGE_WIDTH)
        
    def transfer(self, trgt_acc_no, transfer_amount, v=VERBOSE_MAIN_FUNCTIONS):
        # transfer
        ## Run superclass version of transfer
        ## Display appropriate result
        
        balance = super().transfer(self.id, trgt_acc_no, transfer_amount, v)
        if balance[0] is not False: self.printAccountInfo([self.id, trgt_acc_no], balance[:2], balance[2:], [self.open_date, 'N/A'])
        else:
            if balance[1] == 0: printString("Source Account error", length=DEFAULT_PAGE_WIDTH)
            elif balance[1] == 1: printString("Target Account error", length=DEFAULT_PAGE_WIDTH)
            printString("Transfer unsuccessful", length=DEFAULT_PAGE_WIDTH)


########## Main Program ##########


def main():
    # main
    ### Generate the required objects for running the application
    ## Connect to a MySQL database and generate an object to store all connection data
    ## Generate the Bank Session object and check if there is a connection
    ## if no connection
    ##     do nothing
    ## loop until client likes to exit application
    ##     Display main bank functions
    ##     Get input of which function to run
    ##     Run the function
    
    dbObject = MySQLConnector.mysqlDB(MYSQL_HOST, MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DATABASE)
    
    bankSession = BankSession(dbObject)
    if bankSession.dbObj.getConnection() is False:
        printString("Connection to MySQL DB was UNSUCCESSFUL", length=DEFAULT_PAGE_WIDTH)
        return False
    
    CODE = -1
    # Connection to database was successful
    while CODE and bankSession.dbObj.getConnection() is not False:
        # Display the options
        # Get input based on how you want to interact with the BankSession application
        # Run a function (Create Account, Check Balance, Deposit, Withdraw, Transfer) or exit
        bankSession.displayOptions()
        CODE = getInput(prefix="Enter a code")
        bankSession.selectOption(CODE)
    
    # Connection has ended or failed to connect to database
    printString("Connection has been terminated", length=DEFAULT_PAGE_WIDTH)
    printStatus(STATUS_EXIT, DEBUG)
    return True

if __name__ == "__main__":
    # run the 'main' function
    main()