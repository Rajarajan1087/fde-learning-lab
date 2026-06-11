create table users
(ID int primary key identity(1,1),
Name varchar(50),
Email varchar(50) CHECK (Email LIKE '%_@__%.__%'), 
age  int check(age> 20 and age < 90),
country varchar(30) );

INSERT INTO users (Name, Email , age , country) VALUES ('Aman', 'aman1996@gmail.com',30 , 'India'); 
INSERT INTO users (Name, Email , age , country) VALUES ('Dhiya', 'Dhiya1999@gmail.com',27 , 'India');
INSERT INTO users (Name, Email , age , country) VALUES ('Jennifer', 'Jenny_sg@gmail.com',36 , 'Singapore');
INSERT INTO users (Name, Email , age , country) VALUES ('John', 'jp_architec@gmail.com',45 , 'UK');

select name, email from users;

select * from users where age > 25;

select name from users where Country = 'India';