DROP DATABASE IF EXISTS ngo_connect;

CREATE DATABASE ngo_connect;

DROP TABLE IF EXISTS ngos;

CREATE TABLE ngos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    district VARCHAR(100) NOT NULL,
    address TEXT,
    phone VARCHAR(255),
    mobile VARCHAR(255),
    email VARCHAR(255),
    website VARCHAR(255),
    contact_person VARCHAR(255),
    purpose TEXT,
    mission TEXT,
    url TEXT
);