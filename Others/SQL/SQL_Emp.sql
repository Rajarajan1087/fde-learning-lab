
-- Employees table
CREATE TABLE employees (
    emp_id INT PRIMARY KEY,
    name VARCHAR(40) NOT NULL
);

CREATE TABLE Dept (
    DeptID INT PRIMARY KEY,
    Dept_name VARCHAR(40) NOT NULL
);

	INSERT INTO Dept (DeptID, Dept_name) VALUES
	(30,'Science'),
	(45,'Marketing'),
	(93,'Admin');

/*Write an SQL query to get a list of all employees along with their department names.  
If any employee is not assigned a department, show “Not Assigned”. */

	SELECT 
    e.emp_id,
    e.name,
    ISNULL(d.dept_name, 'Not Assigned') AS dept_name
FROM employees AS e
LEFT JOIN Dept AS d
    ON e.DeptID = d.DeptID;


alter table employees add DeptID int;


UPDATE employees
SET DeptID = ROUND(10 + RAND(CHECKSUM(NEWID())) * 100, 0)
WHERE DeptID IS NULL;

select * from employees;

-- Timesheet table
CREATE TABLE timesheet (
    emp_id INT PRIMARY KEY,
    hours_logged INT NOT NULL
);

-- Employees only (no timesheet)
INSERT INTO employees (emp_id, name) VALUES
(3, 'Shurthi');

-- Timesheet only (no employee record)
INSERT INTO timesheet (emp_id, hours_logged) VALUES
(2, 40),
(3, 35),
(4, 25);





SELECT 
    COALESCE(e.emp_id, t.emp_id) AS emp_id,
    e.name,
    t.hours_logged,
    CASE
        WHEN e.emp_id IS NOT NULL AND t.emp_id IS NOT NULL 
            THEN 'Matched'
        WHEN e.emp_id IS NOT NULL AND t.emp_id IS NULL 
            THEN 'Only in employees'
        WHEN e.emp_id IS NULL AND t.emp_id IS NOT NULL 
            THEN 'Only in timesheet'
    END AS status
FROM employees e
FULL JOIN timesheet t ON e.emp_id = t.emp_id
ORDER BY emp_id;


