# Bank
Bank application using Python and MySQLconnector API to communicate with a MySQL database. This will allow the Bank to manage persistent data and is ACID compliant

## Config
A *config.ini* file is required and must contain login credentials in the following format:<br/><br/>
  \## Start of File ##<br/>
  
  [MYSQL]<br/>
  host = ***yourHostName***<br/>
  username = ***yourUsername***<br/>
  password = ***yourPassword***<br/>
  database = ***yourDatabaseName***<br/>
  
  \## End of File ##<br/>

## MySQL database schema
CREATE TABLE "accounts" (<br/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"account_no" int NOT NULL AUTO_INCREMENT,<br/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"name" varchar(15) NOT NULL,<br/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"balance" int NOT NULL,<br/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"open_date" datetime DEFAULT CURRENT_TIMESTAMP,<br/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;PRIMARY KEY ("account_no"),<br/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;CONSTRAINT "accounts_chk_1" CHECK (("balance" >= 0))<br/>
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;<br/>
