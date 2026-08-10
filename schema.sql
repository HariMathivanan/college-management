CREATE DATABASE IF NOT EXISTS alumni_db;
USE alumni_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','alumni','student','staff') DEFAULT 'alumni',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alumni (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    batch_year YEAR NOT NULL,
    department VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    city VARCHAR(100),
    company VARCHAR(150),
    job_title VARCHAR(150),
    bio TEXT,
    linkedin VARCHAR(200),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    enrollment_year YEAR NOT NULL,
    department VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    roll_number VARCHAR(30),
    bio TEXT,
    skills TEXT,
    linkedin VARCHAR(200),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    department VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    bio TEXT,
    linkedin VARCHAR(200),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    location VARCHAR(200),
    organizer VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    company VARCHAR(150) NOT NULL,
    location VARCHAR(150),
    description TEXT,
    contact_email VARCHAR(150),
    posted_by INT,
    posted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (posted_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    author VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS donations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    donation_status VARCHAR(50) DEFAULT 'Pending',
    payment_method VARCHAR(50),
    donation_type VARCHAR(150),
    phone VARCHAR(30),
    note TEXT,
    razorpay_order_id VARCHAR(100),
    razorpay_payment_id VARCHAR(100),
    razorpay_signature VARCHAR(200),
    payment_status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS donation_allocations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    donation_id INT NOT NULL,
    student_id INT NOT NULL,
    allocated_by INT NULL,
    amount DECIMAL(10,2) NOT NULL,
    note TEXT,
    claimed BOOLEAN DEFAULT 0,
    claimed_at TIMESTAMP NULL,
    allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donation_id) REFERENCES donations(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(user_id) ON DELETE CASCADE,
    FOREIGN KEY (allocated_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS donation_spending (
    id INT AUTO_INCREMENT PRIMARY KEY,
    donation_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    category VARCHAR(100) DEFAULT 'General',
    description TEXT NOT NULL,
    spent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donation_id) REFERENCES donations(id) ON DELETE CASCADE
);

-- Pre-created Admin account (password stored as a secure hash)
INSERT IGNORE INTO users (name, email, password, role) VALUES
('Admin', 'admin@alumni.com', 'scrypt:32768:8:1$wh9k5VEB2gG23xvI$58d67fdefc5e8637fff7e6436b3d562eaee76915cf44c7d310dff7aa539308303cf14ec40fc5732ba250c6f08191fe133cafa3b40289f2f9238c0b1662fe4a0c', 'admin');

INSERT IGNORE INTO alumni (user_id, name, email, batch_year, department) VALUES (1, 'Admin', 'admin@alumni.com', 2015, 'Computer Science');

-- Sample Alumni account (password stored as a secure hash)
INSERT IGNORE INTO users (name, email, password, role) VALUES
('Priya Sharma', 'priya@example.com', 'scrypt:32768:8:1$wh9k5VEB2gG23xvI$58d67fdefc5e8637fff7e6436b3d562eaee76915cf44c7d310dff7aa539308303cf14ec40fc5732ba250c6f08191fe133cafa3b40289f2f9238c0b1662fe4a0c', 'alumni');
INSERT IGNORE INTO alumni (user_id, name, email, batch_year, department, city, company, job_title) VALUES (2, 'Priya Sharma', 'priya@example.com', 2018, 'Computer Science', 'Bangalore', 'Infosys', 'Software Engineer');

-- Sample Student account (password stored as a secure hash)
INSERT IGNORE INTO users (name, email, password, role) VALUES
('Rahul Kumar', 'rahul@example.com', 'scrypt:32768:8:1$wh9k5VEB2gG23xvI$58d67fdefc5e8637fff7e6436b3d562eaee76915cf44c7d310dff7aa539308303cf14ec40fc5732ba250c6f08191fe133cafa3b40289f2f9238c0b1662fe4a0c', 'student');
INSERT IGNORE INTO students (user_id, name, email, enrollment_year, department, roll_number) VALUES (3, 'Rahul Kumar', 'rahul@example.com', 2022, 'Computer Science', 'CS22001');
-- Sample Staff account (password stored as a secure hash)
INSERT IGNORE INTO users (name, email, password, role)VALUES 
('Ram','ram@example.com','scrypt:32768:8:1$wh9k5VEB2gG23xvI$58d67fdefc5e8637fff7e6436b3d562eaee76915cf44c7d310dff7aa539308303cf14ec40fc5732ba250c6f08191fe133cafa3b40289f2f9238c0b1662fe4a0c','staff');
INSERT IGNORE INTO staff (user_id, name, email, department, phone, bio, linkedin)VALUES (LAST_INSERT_ID(),'Ram','ram@example.com','General','','',  '');

INSERT INTO events (title, description, event_date, location, organizer) VALUES
('Annual Alumni Meet 2024', 'Grand reunion with classmates and faculty.', '2024-12-15', 'College Auditorium', 'Alumni Association'),
('Tech Talk: AI in Industry', 'Industry experts share insights on AI careers.', '2024-11-20', 'Seminar Hall B', 'CS Department');

INSERT INTO jobs (title, company, location, description, contact_email, posted_by) VALUES
('Software Engineer', 'TechCorp India', 'Bangalore', 'Python/Flask developer, 2+ years experience.', 'hr@techcorp.com', 2),
('Data Analyst', 'AnalyticsHub', 'Hyderabad', 'SQL, Python, Tableau. 1-3 years experience.', 'careers@analyticshub.com', 2);

INSERT INTO news (title, content, author) VALUES
('Welcome to Alumni Portal', 'We are excited to launch our new alumni management system!', 'Admin'),
('Scholarship Fund Open', 'Applications for the Alumni Scholarship Fund 2024 are now open.', 'Admin');
