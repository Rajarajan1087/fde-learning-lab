create table Students
( id int primary key identity(1,1),
name varchar(20) not null,
class int not null default 10,
subject varchar(20) not null,
city varchar(20) not null default 'Mumbai',
marks int check(marks>0 and marks<101));

INSERT INTO Students (name, class, subject, marks, city) VALUES
('Riya', 10, 'Math', 92, 'Mumbai'),
('Aarav', 10, 'English', 85, 'Delhi'),
('Sneha', 12, 'Math', 76, 'Mumbai'),
('Karan', 12, 'English', 89, 'Chennai'),
('Meena', 10, 'Math', 80, 'Delhi'),
('Rahul', 12, 'English', 95, 'Mumbai');

select name,marks,subject from Students where city = 'Delhi' and subject = 'Math';

select count(*) as TotalStu from Students;

select AVG(marks) from Students;

select sum(marks) as total,subject from Students group by subject;

select Avg(marks) as AvgMarks,class from Students group by class having Avg(marks) > 85;