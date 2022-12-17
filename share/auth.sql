PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

DROP TABLE IF EXISTS "userData";
CREATE TABLE IF NOT EXISTS "userData" (	
	"username"	TEXT UNIQUE CHECK(username!= null),
	"password"	TEXT CHECK(password!= null),
	PRIMARY KEY("username")
);

CREATE INDEX userData_idx ON userData(username);
COMMIT;