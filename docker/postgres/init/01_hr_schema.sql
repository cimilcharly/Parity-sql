-- PostgreSQL HR Schema Initialization for Parity
-- Matches Oracle HR schema structure and seed data for dual-database verification

CREATE SCHEMA IF NOT EXISTS hr;
SET search_path TO hr, public;

-- 1. REGIONS
CREATE TABLE regions (
    region_id INT PRIMARY KEY,
    region_name VARCHAR(25)
);

-- 2. COUNTRIES
CREATE TABLE countries (
    country_id CHAR(2) PRIMARY KEY,
    country_name VARCHAR(40),
    region_id INT REFERENCES regions(region_id)
);

-- 3. LOCATIONS
CREATE TABLE locations (
    location_id INT PRIMARY KEY,
    street_address VARCHAR(40),
    postal_code VARCHAR(12),
    city VARCHAR(30) NOT NULL,
    state_province VARCHAR(25),
    country_id CHAR(2) REFERENCES countries(country_id)
);

-- 4. DEPARTMENTS
CREATE TABLE departments (
    department_id INT PRIMARY KEY,
    department_name VARCHAR(30) NOT NULL,
    manager_id INT,
    location_id INT REFERENCES locations(location_id)
);

-- 5. JOBS
CREATE TABLE jobs (
    job_id VARCHAR(10) PRIMARY KEY,
    job_title VARCHAR(35) NOT NULL,
    min_salary NUMERIC(6, 0),
    max_salary NUMERIC(6, 0)
);

-- 6. EMPLOYEES
CREATE TABLE employees (
    employee_id INT PRIMARY KEY,
    first_name VARCHAR(20),
    last_name VARCHAR(25) NOT NULL,
    email VARCHAR(25) NOT NULL,
    phone_number VARCHAR(20),
    hire_date TIMESTAMP NOT NULL,
    job_id VARCHAR(10) NOT NULL REFERENCES jobs(job_id),
    salary NUMERIC(8, 2),
    commission_pct NUMERIC(2, 2),
    manager_id INT REFERENCES employees(employee_id),
    department_id INT REFERENCES departments(department_id)
);

-- 7. JOB_HISTORY
CREATE TABLE job_history (
    employee_id INT NOT NULL REFERENCES employees(employee_id),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    job_id VARCHAR(10) NOT NULL REFERENCES jobs(job_id),
    department_id INT REFERENCES departments(department_id),
    CONSTRAINT pk_job_history PRIMARY KEY (employee_id, start_date)
);

-- Seed Data: Regions
INSERT INTO regions VALUES (1, 'Europe');
INSERT INTO regions VALUES (2, 'Americas');
INSERT INTO regions VALUES (3, 'Asia');
INSERT INTO regions VALUES (4, 'Middle East and Africa');

-- Seed Data: Countries
INSERT INTO countries VALUES ('US', 'United States of America', 2);
INSERT INTO countries VALUES ('CA', 'Canada', 2);
INSERT INTO countries VALUES ('UK', 'United Kingdom', 1);
INSERT INTO countries VALUES ('DE', 'Germany', 1);
INSERT INTO countries VALUES ('JP', 'Japan', 3);
INSERT INTO countries VALUES ('IN', 'India', 3);

-- Seed Data: Locations
INSERT INTO locations VALUES (1400, '2014 Jabberwocky Rd', '26192', 'Southlake', 'Texas', 'US');
INSERT INTO locations VALUES (1500, '2011 Interiors Blvd', '99236', 'South San Francisco', 'California', 'US');
INSERT INTO locations VALUES (1700, '2004 Charade Rd', '98199', 'Seattle', 'Washington', 'US');
INSERT INTO locations VALUES (1800, '460 Bloor St. W.', 'ON M5S 1X8', 'Toronto', 'Ontario', 'CA');
INSERT INTO locations VALUES (2500, 'Magdalen Centre, The Oxford Science Park', 'OX4 4GA', 'Oxford', 'Oxford', 'UK');

-- Seed Data: Jobs
INSERT INTO jobs VALUES ('AD_PRES', 'President', 20080, 40000);
INSERT INTO jobs VALUES ('AD_VP', 'Administration Vice President', 15000, 30000);
INSERT INTO jobs VALUES ('IT_PROG', 'Programmer', 4000, 10000);
INSERT INTO jobs VALUES ('SA_REP', 'Sales Representative', 6000, 12008);
INSERT INTO jobs VALUES ('ST_CLERK', 'Stock Clerk', 2008, 5000);

-- Seed Data: Departments
INSERT INTO departments VALUES (10, 'Administration', 200, 1700);
INSERT INTO departments VALUES (20, 'Marketing', 201, 1800);
INSERT INTO departments VALUES (50, 'Shipping', 124, 1500);
INSERT INTO departments VALUES (60, 'IT', 103, 1400);
INSERT INTO departments VALUES (80, 'Sales', 149, 2500);
INSERT INTO departments VALUES (90, 'Executive', 100, 1700);

-- Seed Data: Employees
INSERT INTO employees VALUES (100, 'Steven', 'King', 'SKING', '515.123.4567', '2003-06-17 09:00:00', 'AD_PRES', 24000.00, NULL, NULL, 90);
INSERT INTO employees VALUES (101, 'Neena', 'Kochhar', 'NKOCHHAR', '515.123.4568', '2005-09-21 09:30:00', 'AD_VP', 17000.00, NULL, 100, 90);
INSERT INTO employees VALUES (102, 'Lex', 'De Haan', 'LDEHAAN', '515.123.4569', '2001-01-13 08:45:00', 'AD_VP', 17000.00, NULL, 100, 90);
INSERT INTO employees VALUES (103, 'Alexander', 'Hunold', 'AHUNOLD', '590.423.4567', '2006-01-03 10:15:00', 'IT_PROG', 9000.00, NULL, 102, 60);
INSERT INTO employees VALUES (104, 'Bruce', 'Ernst', 'BERNST', '590.423.4568', '2007-05-21 11:00:00', 'IT_PROG', 6000.00, NULL, 103, 60);
INSERT INTO employees VALUES (105, 'David', 'Austin', 'DAUSTIN', '590.423.4569', '2005-06-25 09:00:00', 'IT_PROG', 4800.00, NULL, 103, 60);
INSERT INTO employees VALUES (149, 'Eleni', 'Zlotkey', 'EZLOTKEY', '011.44.1344.429018', '2008-01-29 14:00:00', 'SA_REP', 10500.00, 0.20, 100, 80);
INSERT INTO employees VALUES (174, 'Ellen', 'Abel', 'EABEL', '011.44.1644.429267', '2004-05-11 13:15:00', 'SA_REP', 11000.00, 0.30, 149, 80);
INSERT INTO employees VALUES (178, 'Kimberely', 'Grant', 'KGRANT', '011.44.1644.429263', '2007-05-24 10:00:00', 'SA_REP', 7000.00, 0.15, 149, NULL);

-- Seed Data: Job History
INSERT INTO job_history VALUES (102, '2001-01-13', '2006-07-24', 'IT_PROG', 60);
INSERT INTO job_history VALUES (101, '1997-09-21', '2001-10-27', 'AD_VP', 90);
