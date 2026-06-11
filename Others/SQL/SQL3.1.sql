create table Students
( id int primary key identity(1000,1),
name varchar(20),
grade int check(grade>0 and grade<101));

alter table Students add age int;
update Students set age= 8 where age is null


INSERT INTO Students (name, grade) VALUES ('Aman', 95); 
INSERT INTO Students (name, grade) VALUES ('Dhiya', 99); 
INSERT INTO Students (name, grade) VALUES ('PadmaPriya', 98); 


select * from Students;

select count(*) from Students
select AVG(marks) as avgmarks from Students

select MIN(marks) as Minmarks,MAX(marks) as Maxmarks  from Students

create table Courses
( course_id int primary key identity(1,1),
course_name varchar(20));

create table Enrollments 
( course_id int references courses(course_id),
Student_id int references students(id));

INSERT INTO Students (name, marks,grade,city,age) VALUES ('Dhawan', 67, 'C','Trichy', 6 ); 
INSERT INTO Students (name, grade) VALUES ('Tamizhini', 97); 
 
 INSERT INTO Courses(course_name) VALUES ('English'); 
 INSERT INTO Courses (course_name) VALUES ('Maths'); 
 INSERT INTO Courses (course_name) VALUES ('Science'); 

 select * from Courses;
 select * from Students;

 INSERT INTO Enrollments (course_id,Student_id) VALUES (1,1000); 
 INSERT INTO Enrollments (course_id,Student_id) VALUES (1,1001); 
 INSERT INTO Enrollments (course_id,Student_id) VALUES (1,1002); 
 INSERT INTO Enrollments (course_id,Student_id) VALUES (1,1003); 
 INSERT INTO Enrollments (course_id,Student_id) VALUES (2,1001); 
 INSERT INTO Enrollments (course_id,Student_id) VALUES (2,1002);  
  INSERT INTO Enrollments (course_id,Student_id) VALUES (3,1000); 
 INSERT INTO Enrollments (course_id,Student_id) VALUES (3,1001);  
 INSERT INTO Enrollments (course_id,Student_id) VALUES (3,1003); 


 select s.name, c.course_name from Enrollments e inner join Students s on e.Student_id = s.id inner join Courses c on e.course_id = c.course_id;


 EXEC sp_rename 'Students.grade', 'marks', 'COLUMN';

 SELECT cc.name
FROM sys.check_constraints cc
JOIN sys.columns c
    ON cc.parent_object_id = c.object_id
WHERE cc.parent_object_id = OBJECT_ID('Students')
  AND c.name = 'grade';

  ALTER TABLE Students
DROP CONSTRAINT CK__Students__grade__6FE99F9F;

  ALTER TABLE Students
add grade char(1), city varchar(30);

select * from Students;

update students set marks = 80 where name = 'Aman';
update students set marks = 89 where name = 'Tamizhini';

update students set city = 'Mumbai' where name = 'Aman';
update students set grade = 'B' where name = 'Aman';

select name from Students where marks >85;

select * from Students where grade = 'A' and marks >90;

create table exam_results_2026	
( result_id int primary key identity(2026,1),
student_id int references students(id),
subject varchar(20),
marks int check(marks>0 and marks<101));

 INSERT INTO exam_results_2026(Student_id,subject,marks) VALUES (1000,'Maths',91); 
 INSERT INTO exam_results_2026(Student_id,subject,marks) VALUES (1000,'Science',78);
 INSERT INTO exam_results_2026(Student_id,subject,marks) VALUES (1001,'Maths',98); 
 INSERT INTO exam_results_2026(Student_id,subject,marks) VALUES (1001,'Science',98);
 INSERT INTO exam_results_2026(Student_id,subject,marks) VALUES (1002,'Maths',87); 
 INSERT INTO exam_results_2026(Student_id,subject,marks) VALUES (1002,'Science',79);
 INSERT INTO exam_results_2026(Student_id,subject,marks) VALUES (1003,'Maths',89); 
 INSERT INTO exam_results_2026(Student_id,subject,marks) VALUES (1003,'Science',72);

 select s.name,e.subject,e.marks from exam_results_2026 e inner join 
 Students s on e.student_id = s.id where e.subject = 'Maths' order by e.marks desc; 

  select top 3 s.name,e.subject,e.marks from exam_results_2026 e inner join 
 Students s on e.student_id = s.id where e.subject = 'Science' order by e.marks desc ; 

 SELECT s.id, s.name, e.subject, e.marks
FROM exam_results_2026 e
JOIN Students s ON e.student_id = s.id
ORDER BY e.subject ASC, e.marks DESC;

select * from exam_results_2026;

alter table Students add class int;

update Students set class= 4 where id = 1005

with stuExam2026 as (
 SELECT s.id, s.name, s.class, e.subject, e.marks
FROM exam_results_2026 e
JOIN Students s ON e.student_id = s.id
)
select class , subject, sum(marks) as TotalMarks from stuExam2026 group by subject,class;

select class , avg(marks) as AvgMarks,count(*)  from Students group by class having avg(marks) > 85;



