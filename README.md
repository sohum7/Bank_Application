# Bank
Bank Application using Python and MySQL database

## Config
A config.ini file is required in the following format:<br/><br/>
[MYSQL]<br/>
host = ...<br/>
username = ...<br/>
password = ...<br/>
database = ...<br/>

## MySQL database schema
CREATE TABLE `accounts` (<br/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`account_no` int NOT NULL AUTO_INCREMENT,<br/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`name` varchar(15) NOT NULL,<br/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`balance` int NOT NULL,<br/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`open_date` datetime DEFAULT CURRENT_TIMESTAMP,<br/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;PRIMARY KEY (`account_no`),<br/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;CONSTRAINT `accounts_chk_1` CHECK ((`balance` >= 0))<br/>
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;<br/>
