DROP DATABASE IF EXISTS ngo_connect;

CREATE DATABASE ngo_connect;

USE ngo_connect;

CREATE TABLE ngos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    phone VARCHAR(255),
    mobile VARCHAR(255),
    email VARCHAR(255),
    website VARCHAR(255),
    contact_person VARCHAR(255),
    purpose TEXT,
    mission TEXT,
    url VARCHAR(500) UNIQUE
);