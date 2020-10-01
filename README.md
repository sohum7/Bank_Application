# Bank
Bank Application using Python and MySQL database

## Config
A config.ini file is required in the following format:<br/>
[MYSQL]<br/>
host = ...<br/>
username = ...<br/>
password = ...<br/>
database = ...<br/>

## MySQL database schema
CREATE TABLE `accounts` (
  `account_no` int NOT NULL AUTO_INCREMENT,
  `name` varchar(15) NOT NULL,
  `balance` int NOT NULL,
  `open_date` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_no`),
  CONSTRAINT `accounts_chk_1` CHECK ((`balance` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
