CREATE DATABASE knowledge_trading_erp;
USE knowledge_trading_erp;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('Admin','Faculty','Staff') NOT NULL
);
INSERT INTO users(username,password,role)
VALUES
('admin','admin123','Admin');
SELECT * FROM users;