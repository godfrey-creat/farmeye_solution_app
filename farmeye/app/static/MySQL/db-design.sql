-- Create and select the FarmEye database
CREATE DATABASE IF NOT EXISTS farmeye;
USE farmeye;

-- Users table (1:N relationship with Farms)
CREATE TABLE Users (
    user_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    farm_size DECIMAL(10,2),
    farm_location POINT,
    user_type ENUM('smallholder', 'commercial', 'cooperative') NOT NULL,
    subscription_tier VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Farms table (N:1 relationship with Users, 1:N relationship with Fields)
CREATE TABLE Farms (
    farm_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    farm_name VARCHAR(100) NOT NULL,
    farm_size DECIMAL(10,2) NOT NULL COMMENT 'in acres',
    farm_location POINT NOT NULL,
    soil_type VARCHAR(50),
    elevation DECIMAL(8,2),
    created_at TIMESTAMP NOT NULL,
    last_updated TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    SPATIAL INDEX(farm_location)
);

-- Store farm boundaries as polygon data
CREATE TABLE FarmBoundaries (
    boundary_id VARCHAR(36) PRIMARY KEY,
    farm_id VARCHAR(36) NOT NULL,
    boundary POLYGON NOT NULL,
    FOREIGN KEY (farm_id) REFERENCES Farms(farm_id) ON DELETE CASCADE,
    SPATIAL INDEX(boundary)
);

-- Fields table (N:1 relationship with Farms, 1:N relationship with SensorData and AnalysisResults)
CREATE TABLE Fields (
    field_id VARCHAR(36) PRIMARY KEY,
    farm_id VARCHAR(36) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    field_size DECIMAL(10,2) NOT NULL COMMENT 'in acres',
    crop_type VARCHAR(50),
    planting_date TIMESTAMP,
    expected_harvest_date TIMESTAMP,
    current_growth_stage VARCHAR(50),
    intercropping BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (farm_id) REFERENCES Farms(farm_id) ON DELETE CASCADE
);

-- Store field boundaries as polygon data
CREATE TABLE FieldBoundaries (
    boundary_id VARCHAR(36) PRIMARY KEY,
    field_id VARCHAR(36) NOT NULL,
    boundary POLYGON NOT NULL,
    FOREIGN KEY (field_id) REFERENCES Fields(field_id) ON DELETE CASCADE,
    SPATIAL INDEX(boundary)
);

-- Sensors table (to track physical sensors)
CREATE TABLE Sensors (
    sensor_id VARCHAR(36) PRIMARY KEY,
    field_id VARCHAR(36) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    installation_date TIMESTAMP NOT NULL,
    status ENUM('active', 'inactive', 'maintenance') DEFAULT 'active',
    last_maintenance TIMESTAMP,
    FOREIGN KEY (field_id) REFERENCES Fields(field_id) ON DELETE CASCADE
);

-- SensorData table (N:1 relationship with Fields, contains all sensor readings)
CREATE TABLE SensorData (
    reading_id VARCHAR(36) PRIMARY KEY,
    field_id VARCHAR(36) NOT NULL,
    sensor_id VARCHAR(36) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    sensor_type VARCHAR(50) NOT NULL COMMENT 'soil, temp, humidity, etc.',
    value DECIMAL(10,4) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    location POINT NOT NULL, -- Changed to NOT NULL to support SPATIAL INDEX
    battery_level DECIMAL(5,2),
    reading_quality ENUM('good', 'suspect', 'error') DEFAULT 'good',
    FOREIGN KEY (field_id) REFERENCES Fields(field_id) ON DELETE CASCADE,
    FOREIGN KEY (sensor_id) REFERENCES Sensors(sensor_id) ON DELETE CASCADE,
    INDEX (timestamp),
    INDEX (sensor_type),
    SPATIAL INDEX(location)
);
-- AnalysisResults table (N:1 relationship with Fields)
CREATE TABLE AnalysisResults (
    analysis_id VARCHAR(36) PRIMARY KEY,
    field_id VARCHAR(36) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    analysis_type VARCHAR(50) NOT NULL COMMENT 'crop health, weed detection, etc.',
    data_source VARCHAR(50) NOT NULL COMMENT 'satellite, cctv, sensor',
    confidence_score DECIMAL(5,2) NOT NULL COMMENT 'scale of 0-100',
    image_url VARCHAR(255),
    action_required BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (field_id) REFERENCES Fields(field_id) ON DELETE CASCADE,
    INDEX (timestamp),
    INDEX (analysis_type)
);

-- Store analysis results in JSON format
CREATE TABLE AnalysisResultsData (
    analysis_id VARCHAR(36) PRIMARY KEY,
    results JSON NOT NULL,
    FOREIGN KEY (analysis_id) REFERENCES AnalysisResults(analysis_id) ON DELETE CASCADE
);

-- Store recommendations separately
CREATE TABLE Recommendations (
    recommendation_id VARCHAR(36) PRIMARY KEY,
    analysis_id VARCHAR(36) NOT NULL,
    recommendation TEXT NOT NULL,
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    status ENUM('pending', 'in_progress', 'completed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES AnalysisResults(analysis_id) ON DELETE CASCADE
);

-- Images table to store references to captured images
CREATE TABLE Images (
    image_id VARCHAR(36) PRIMARY KEY,
    field_id VARCHAR(36) NOT NULL,
    capture_time TIMESTAMP NOT NULL,
    image_type ENUM('aerial', 'ground', 'satellite', 'sensor') NOT NULL,
    url VARCHAR(255) NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (field_id) REFERENCES Fields(field_id) ON DELETE CASCADE,
    INDEX (capture_time)
);

-- Weather data for each farm
CREATE TABLE WeatherData (
    weather_id VARCHAR(36) PRIMARY KEY,
    farm_id VARCHAR(36) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    rainfall DECIMAL(6,2),
    wind_speed DECIMAL(5,2),
    forecast JSON,
    FOREIGN KEY (farm_id) REFERENCES Farms(farm_id) ON DELETE CASCADE,
    INDEX (timestamp)
);

-- Create necessary indices for performance
CREATE INDEX idx_farms_user_id ON Farms(user_id);
CREATE INDEX idx_fields_farm_id ON Fields(farm_id);
CREATE INDEX idx_sensor_data_field_id ON SensorData(field_id);
CREATE INDEX idx_analysis_results_field_id ON AnalysisResults(field_id);

-- Add notifications table for alerts
CREATE TABLE Notifications (
    notification_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    field_id VARCHAR(36),
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (field_id) REFERENCES Fields(field_id) ON DELETE SET NULL
);

-- Add AI models table to track model versions
CREATE TABLE AIModels (
    model_id VARCHAR(36) PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    accuracy DECIMAL(5,2),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY (model_name, model_version)
);