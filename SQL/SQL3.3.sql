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



create table Stu
(roll_no  int primary key identity(1,1),
name varchar(40) not null);

create table Mar
(roll_no  int primary key references Stu(roll_no),
marks int not null check(marks>0 and marks<101));


-- Table 1: Stu
insert into Stu(name) values
('Riya'),
('Ayaan'),
('Sneha'),
('Arjun');

-- Table 2: Mar
insert into Mar(roll_no, marks) values
(1, 88),
(2, 72),
(4, 95);

select count(s.name) as NoOfStuWitMarks from Stu s inner join Mar m on s.roll_no= m.roll_no 
where m.marks > 75 order by m.marks desc;

alter table Mar add subject varchar(20) not null default('Maths');

select * from Mar;

update Mar set subject = ' English' where marks < 90;

/*Into model DB*/
drop table sales;
create table sales 
(sale_id int primary key identity(101,1),
product_id int ,
amount float not null);

create table products 
(product_id int primary key not null,
product_name varchar(50) not null);

-- Insert products
INSERT INTO products (product_id, product_name) VALUES
(1, 'Laptop'),
(2, 'Mouse'),
(3, 'Keyboard');

-- Insert sales (including one with missing product)
INSERT INTO sales ( product_id, amount) VALUES
( 1, 50000),
( 2, 500),
( 3, 1500),
( 999, 200);   -- product_id 999 does not exist in products


select * from products p right join sales s on p.product_id = s.product_id;



-- Table A: customers
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(40) NOT NULL
);

-- Table B: orders
CREATE TABLE orders (
    customer_id INT,
    order_id  INT PRIMARY KEY
);

-- Insert into customers
INSERT INTO customers (customer_id, name) VALUES
(21 ,'AARA'),
(22 ,'BAARA'),
(23, 'KAARA'),
(24 ,'RAARA'),
(25 ,'TAARA'),
(26, 'DAARA'),
(27 ,'QAARA'),
(28 ,'VAARA'),
(29, 'MAARA');
-- Insert into orders
INSERT INTO orders (customer_id, order_id) VALUES
(4, 104),
(6, 106);

select * from customers c left join orders o on c.customer_id = o.customer_id ;
/*where c.name is null or o.customer_id is null;*/

/*?	a) List all customers and their order amounts (include customers with no orders). */

select c.customer_id, c.name,c.city,o.order_id,o.amount from customers c 
left join orders o on c.customer_id = o.customer_id where order_id is not null;

select * from orders;
alter table customers add city varchar(20);

alter table orders add amount DECIMAL(10, 2);


UPDATE customers
SET city = null
WHERE city IS NOT NULL;

UPDATE customers
SET city = CHOOSE(
    CAST(RAND(CHECKSUM(NEWID())) * 4 AS INT) + 1,
    'Madurai',
    'Chennai',
    'Bangalore',
	'Thanjavur'
)
WHERE city IS NULL;

UPDATE orders
SET amount = ROUND(10 + RAND(CHECKSUM(NEWID())) * 290, 2)
WHERE amount IS NULL;


select * from products;
select * from orders;
select * from customers;


--insert 10 random line for oprders in order table for 9 cutsomers

WITH n AS (
    SELECT TOP (9)
        ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS rn
    FROM sys.objects
)
INSERT INTO orders (customer_id, order_id, amount, product_id, purchase_date)
SELECT
    21 + ABS(CHECKSUM(NEWID())) % 9,
    150 + rn,
    CAST(1000 + (ABS(CHECKSUM(NEWID())) % 390001) / 100.0 AS DECIMAL(10,2)),
    1 + ABS(CHECKSUM(NEWID())) % 3,
    DATEADD(DAY, ABS(CHECKSUM(NEWID())) % (DATEDIFF(DAY, '2026-06-01', GETDATE()) + 1), '2026-06-01')
FROM n
WHERE 150 + rn <= 999;


--b.	Identify customers who made purchases in at least 3 different months (use 
-- COUNT(DISTINCT MONTH(date))  ) 

SELECT c.customer_id, c.name, COUNT(DISTINCT MONTH(o.purchase_date)) as total_months_active
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(DISTINCT MONTH(o.purchase_date)) >= 3;

--c.	Compare total revenue between first-time and repeat customers using  CASE  and  GROUP BY 

WITH firstPurchase AS (
    SELECT customer_id, MIN(purchase_date) AS first_order
    FROM orders
    GROUP BY customer_id
)
SELECT
    customer_type,
    COUNT(*) AS total_orders,
    COUNT(DISTINCT customer_id) AS total_customers,
    SUM(amount) AS total_revenue
FROM (
    SELECT
        o.amount,
        o.customer_id,
        CASE
            WHEN o.purchase_date = fp.first_order THEN 'NEW'
            ELSE 'RETURNING'
        END AS customer_type
    FROM orders o
    JOIN firstPurchase fp
        ON o.customer_id = fp.customer_id
) t
GROUP BY customer_type;


--New vs returinig count


WITH latest_date AS (
    SELECT MAX(purchase_date) AS max_date
    FROM orders
),
customer_flags AS (
    SELECT
        o.customer_id,
        CASE
            WHEN COUNT(CASE WHEN o.purchase_date < ld.max_date THEN 1 END) > 0 THEN 'RETURNING'
            ELSE 'NEW'
        END AS customer_type
    FROM orders o
    CROSS JOIN latest_date ld
    GROUP BY o.customer_id, ld.max_date
)
SELECT
    cf.customer_type,
    COUNT(*) AS total_customers
FROM customer_flags cf
GROUP BY cf.customer_type;





update orders set product_id = 1, purchase_date = DATEADD(day, -25, GETDATE())
where customer_id = 6

select * from orders;

update orders set customer_id = 27 where order_id = 157




ALTER TABLE orders
ADD product_id INT;

ALTER TABLE orders
ADD purchase_date DATE;

ALTER TABLE orders
ADD CONSTRAINT fk_orders_products
FOREIGN KEY (product_id) REFERENCES products(product_id);


SELECT top 2 o.product_id , p.product_name,sum(o.amount) as total_amount
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
WHERE o.purchase_date >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) - 1, 0)
  AND o.purchase_date <  DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0)
GROUP BY o.product_id, p.product_name order by sum(amount) desc;


--Model DB

create table stud
(roll_no int primary key identity(1,1),
name varchar(30));

create table submis
(roll_no int primary key references stud(roll_no),
status varchar(30) default('Submitted'));

insert into stud (name) values 
('Riya'),
('Ayaan '),
('Priya '),
('Meena ');

insert into submis(roll_no) values 
(1),
(2),
(3);

select COALESCE(s.roll_no,su.roll_no),name,status,subject
from stud s left join submis su on s.roll_no = su.roll_no order by status desc,name;

select COALESCE(s.roll_no,su.roll_no),name,subject
from stud s left join submis su on s.roll_no = su.roll_no where status is not null order by status desc,name ;

alter table submis add subject varchar(10) default('Maths');
alter table submis drop column subject ;
alter table submis drop PK__submis__9560EEE1CAFA0167 ; 

update submis set subject = 'English' where roll_no =2
