import MysqlConnector
import time
import configparser
import logging
import sys

# Defaults
DEFAULT_PAGE_WIDTH = 100
DEFAULT_ACCOUNT_NAME = "John Doe"
DEFAULT_BALANCE = 0

# Debugger
DEBUG = 0
VERBOSE_MAIN_FUNCTIONS = 0

# Logging
logging.basicConfig(filename='bank.log', format='%(asctime)s - Process ID: %(process)d ---- %(levelname)s ---- %(message)s', datefmt='%d-%b-%y %H:%M:%S')

# Status of requests
STATUS_START = 1
STATUS_LOAD = 2
STATUS_COMP = 3
STATUS_EXIT = 4
STATUS_ERROR = 0

# Users selected code
CODE = -1

# Credentials File
CRED_FILE = "config.ini"

config = configparser.ConfigParser()
config.read(CRED_FILE)

# Credentials
MYSQL_HOST = config["MYSQL"]["host"]
MYSQL_USERNAME = config["MYSQL"]["username"]
MYSQL_PASSWORD = config["MYSQL"]["password"]
MYSQL_DATABASE = config["MYSQL"]["database"]


########## Useful functions for displaying and retrieving input #############

# print strings
def printString(string="", prefix="\n", suffix="\n", length=50):
    left_ext = right_ext = 0
    # if length is larger than str and not empty
    if length > len(string)+1 and string:
        left_ext = right_ext = (length - len(string)) // 2
        if length % 2: left_ext += 1
    print(f'{prefix}{left_ext*"-"}{string}{right_ext*"-"}{suffix}')

# Print the current status
def printStatus(code, v=1):
    if v:
        if code == 1: printString("Starting...", length=0)
        elif code == 2: printString("Loading...", length=0)
        elif code == 3: printString("Complete.", length=0)
        elif code == 4: printString("Exiting.", length=0)
        else: printString("ERROR.", length=0)

# Retrieve integer input and check for non-int type
def getInput(inputType=int, prefix="", sep=": "):
    output = None
    while (True):
        try:
            output = inputType(input(f"{prefix}{sep}"))
            break
        except (ValueError, TypeError): printString("Please try again.", prefix="", length=0)
    return output

## Get Account Number
def getAccountNumber(string="Account Number"):
    return getInput(inputType=int, prefix=string, sep=": ")

# Displays options for the customer to use
def display_options():
    printString("Main Menu", length=DEFAULT_PAGE_WIDTH)
    print("1 - Create an Account\n"
    + "2 - Check Balance\n"
    + "3 - Desposit\n"
    + "4 - Withdraw\n"
    + "5 - Transfer\n"
    + "0 - Save and Exit\n")


########### Get input based on chosen functionality ############


# Allows customer to pick an option
def select_option(db, code):
    printStatus(STATUS_START, DEBUG)
    # Create Account
    if code == 1:
        acc_name = getInput(str, "Enter an Account Name")
        balance = getInput(prefix="Enter initial balance")
        createAccount(db, acc_name, balance)
    elif 1 < code < 5:
        acc_no = getAccountNumber()
        
        # Check Balance
        if code == 2: checkBalance(db, acc_no)
        # Deposit
        elif code == 3:
            deposit_amount = getInput(prefix="Deposit Amount")
            deposit(db, acc_no, deposit_amount)
        # Withdraw
        elif code == 4:
            withdraw_amount = getInput(prefix="Withdraw Amount")
            withdraw(db, acc_no, withdraw_amount)
    # Transfer
    elif code == 5:
        src_acc_no = getAccountNumber("Source Account Number")
        trgt_acc_no = getAccountNumber("Target Account Number")
        transfer_amount = getInput(prefix="Transfer Amount")
        transfer(db, src_acc_no, trgt_acc_no, transfer_amount)
    # Disconnect
    elif code == 0: db.disconnectDB(MysqlConnector.SAVE_ON_DISCONNECT)
    # Display options again
    else: 
        printString("Invalid code - Please try again", length=DEFAULT_PAGE_WIDTH)


    
def addAccount(db, name, balance):
    db.getCursor().execute("INSERT INTO accounts (name, balance) VALUES (%s, %s);", (name, int(balance)))

def selectRowByAccNbr(db, acc_no, lock=False):
    query = "SELECT * FROM accounts WHERE account_no = %s"
    query += " FOR UPDATE;" if lock else ";"
    db.getCursor().execute(query, (int(acc_no),))

def startTransaction(db):
    db.getCursor().execute("START TRANSACTION;", ())

def updateRowBalanceByAccNbr(db, acc_no, balance):
    db.getCursor().execute("UPDATE accounts SET balance=%s WHERE account_no=%s;", (int(balance), int(acc_no)))

def getBalance(db, acc_no):
    db.getCursor().execute("SELECT balance FROM accounts WHERE account_no = %s;", (int(acc_no),))

def saveTransaction(db):
    db.save()

def rollbackTransaction(db):
    db.rollback()

def getAccountInfo(db, acc_no, balanceOnly=False, v=0):
    try:
        selectRowByAccNbr(db, acc_no)
    except Exception as e:
        printString("Database Error", length=DEFAULT_PAGE_WIDTH)
        logging.error(e)
        raise Exception()
    else:
        row = db.getCursor().fetchone()
        if row is None:
            logging.error(f"The account, with id = {acc_no}, does not exist")
            raise Exception("Account does not exist")
        # row[1] = name
        # row[2] = balance
        # row[3] = open date
        if v:
            print(f"Name:         {row[1]}\n"
                + f"Balance:      {row[2]}\n"
                + f"Opening Date: {row[3]}\n")
            
        logging.debug(f"Fetching account {acc_no} was successful")
        
        return row[2] if balanceOnly else row[1], row[2], row[3]

########## Main functions of the Bank: Create Account, Check Balance, Deposit, Withdraw, Transfer ##########



## Create Account
def createAccount(db, name=DEFAULT_ACCOUNT_NAME, balance=DEFAULT_BALANCE, v=VERBOSE_MAIN_FUNCTIONS):
    printStatus(STATUS_LOAD, DEBUG)
    
    if v: 
        print("Create Account")
        print(f"acc_no: {name}")
        print(f"balance: {balance}")
    
    try:
        startTransaction(db)
        addAccount(db, name, balance)
        saveTransaction(db)
        
        printString("Account successfully created", length=DEFAULT_PAGE_WIDTH)
        
        printStatus(STATUS_COMP, DEBUG)
        
        logging.debug(f"Account creation for '{name}' was successful")
        return True
    except Exception as e:
        rollbackTransaction(db)
        logging.error(e)
    
    printString("Account creation unsuccessful", length=DEFAULT_PAGE_WIDTH)
    printStatus(STATUS_ERROR, DEBUG)
    
    return False

## Check balance
def checkBalance(db, acc_no, v=VERBOSE_MAIN_FUNCTIONS):

    printStatus(STATUS_LOAD, DEBUG)
    
    if v: 
        print("Check Balance")
        print(f"acc_no: {acc_no}")

    # Fetch account information if it exists and display
    try:
        getAccountInfo(db, acc_no, v=1)
        printStatus(STATUS_COMP, DEBUG)
        
        logging.debug(f"Checking balance (Account Id: {acc_no}) was successful")
        
        return True
    except Exception as e:
        logging.error(e)
        
    printString("Check Balance unsuccessful", length=DEFAULT_PAGE_WIDTH)
    printStatus(STATUS_ERROR, DEBUG)
    
    return False

# Deposit Main
def depositMain(db, acc_no, balance, deposit_amount):
    selectRowByAccNbr(db, acc_no, lock=True)
    balance += deposit_amount
    updateRowBalanceByAccNbr(db, acc_no, balance)
    
    return balance

## Deposit
def deposit(db, acc_no, deposit_amount, v=VERBOSE_MAIN_FUNCTIONS):
    printStatus(STATUS_LOAD, DEBUG)
    
    if v: 
        print("Deposit")
        print(f"acc_no: {acc_no}")
        print(f"deposit_amount: {deposit_amount}")
    
    if deposit_amount > 0:
        try:
            balance = getAccountInfo(db, acc_no, balanceOnly=True, v=1)
            
            startTransaction(db)
            balance = depositMain(db, acc_no, balance[0], deposit_amount)
            saveTransaction(db)

            printString(str(balance), prefix="\nNew Balance: ", length=0)
            printStatus(STATUS_COMP, DEBUG)
            
            logging.debug(f"Deposit (Account Id: {acc_no}) was successful")
            
            return True
        except Exception as e:
            rollbackTransaction(db)
            logging.error(e)
        
    printString("Deposit unsuccessful", length=DEFAULT_PAGE_WIDTH)
    printStatus(STATUS_ERROR, DEBUG)
    
    return False

# Withdraw Main
def withdrawMain(db, acc_no, balance, withdraw_amount):
    selectRowByAccNbr(db, acc_no, lock=True)
    balance -= withdraw_amount
    updateRowBalanceByAccNbr(db, acc_no, balance)
    
    return balance

## Withdraw
def withdraw(db, acc_no, withdraw_amount, v=VERBOSE_MAIN_FUNCTIONS):
    ## Get Account data
    ##   if account does not exist OR the withdraw amount is not valid
    ##      then print appropriate message
    ##   else withdraw money from account
    ##      if error occurs, rollback the transaction and print error message
    printStatus(STATUS_LOAD, DEBUG)
    
    if v: 
        print("Withdraw")
        print(f"acc_no: {acc_no}")
        print(f"withdraw_amount: {withdraw_amount}")

    if(0 < withdraw_amount):
        try:
            balance = getAccountInfo(db, acc_no, balanceOnly=True, v=1)
            
            startTransaction(db)
            balance = withdrawMain(db, acc_no, balance[0], withdraw_amount)
            saveTransaction(db)
            
            printString(str(balance), prefix="\nNew Balance: ", length=0)
            printStatus(STATUS_COMP, DEBUG)
            
            logging.debug(f"Withdraw (Account Id: {acc_no}) was successful")
                
            return True
        except Exception as e:
            rollbackTransaction(db)
            logging.error(e)
    
    printString("Withdraw Unsuccessful", prefix="\n", suffix="\n", length=DEFAULT_PAGE_WIDTH)
    printStatus(STATUS_ERROR, DEBUG)
    
    return False     

## Transfer
def transfer(db, src_acc_no, trgt_acc_no, transfer_amount, v=VERBOSE_MAIN_FUNCTIONS):
    printStatus(STATUS_LOAD, DEBUG)
    
    if v: 
        print("Transfer")
        print(f"source_acc_no: {src_acc_no}")
        print(f"target_acc_no: {trgt_acc_no}")
        print(f"deposit_amount: {transfer_amount}")

    switch = 0
    if transfer_amount > 0:
        try:
            src_name, src_balance, src_open_date = getAccountInfo(db, src_acc_no)
            switch += 1
            
            trgt_name, trgt_balance, trgt_open_date = getAccountInfo(db, trgt_acc_no)
            switch += 1
            
            startTransaction(db)
            src_balance = withdrawMain(db, src_acc_no, src_balance, transfer_amount)
            trgt_balance = depositMain(db, trgt_acc_no, trgt_balance, transfer_amount)
            saveTransaction(db)

            printString(str(src_balance), prefix=f"\n{src_name}'s New Balance: ", length=0)
            printString(str(trgt_balance), prefix=f"\n{trgt_name}Target's New Balance: ", length=0)
            printStatus(STATUS_COMP, DEBUG)
            
            logging.debug(f"Transfer from (Account Id: {src_acc_no}) to (Account Id: {trgt_acc_no}) was successful")
            
            return True
        except Exception as e:
            rollbackTransaction(db)
            logging.error(e)
            if switch == 0: printString("Source Account error", length=DEFAULT_PAGE_WIDTH)
            elif switch == 1: printString("Target Account error", length=DEFAULT_PAGE_WIDTH)
    
    printString("Transfer Unsuccessful", length=DEFAULT_PAGE_WIDTH)
    printStatus(STATUS_ERROR, DEBUG)
    
    return False



########## Main Program ##########


if __name__ == "__main__":
    db = MysqlConnector.mysqlDB(MYSQL_HOST, MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DATABASE)
    
    if db.getConnection():
        cursor = db.getNewCursor()
        if cursor:
            while (CODE):
                display_options()
                CODE = getInput(prefix="Enter a code")
                select_option(db, CODE)
    
    printString("Connection has end", length=DEFAULT_PAGE_WIDTH)
    printStatus(STATUS_EXIT, DEBUG)
