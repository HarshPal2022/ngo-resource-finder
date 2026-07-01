CREATE DATABASE IF NOT EXISTS ngo_finder;

USE ngo_finder;

CREATE TABLE IF NOT EXISTS ngos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(100),
    description TEXT,
    contact VARCHAR(100),
    email VARCHAR(255),
    website VARCHAR(255)
);