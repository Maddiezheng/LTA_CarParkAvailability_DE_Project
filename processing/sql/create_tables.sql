-- Create carpark_availability table
CREATE TABLE IF NOT EXISTS carpark_availability (
    id SERIAL PRIMARY KEY,
    CarParkID VARCHAR(50) NOT NULL,
    Area VARCHAR(100),
    Development VARCHAR(255),
    AvailableLots INTEGER,
    LotType VARCHAR(10),
    Agency VARCHAR(50),
    timestamp TIMESTAMP,
    Latitude DOUBLE PRECISION,
    Longitude DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on frequently queried columns
CREATE INDEX IF NOT EXISTS idx_carpark_id ON carpark_availability(CarParkID);
CREATE INDEX IF NOT EXISTS idx_timestamp ON carpark_availability(timestamp);
CREATE INDEX IF NOT EXISTS idx_area ON carpark_availability(Area);