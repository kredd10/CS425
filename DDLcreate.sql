-- Phase II – SQL Script of the ER-Model Translation

-- 1. Users (base for Agent and Prospective Renter)
CREATE TABLE Users (
    User_ID           SERIAL PRIMARY KEY,
    First_name        VARCHAR(250) NOT NULL,
    Last_name         VARCHAR(250) NOT NULL,
    Phone_number      VARCHAR(20),
    Email             VARCHAR(250) UNIQUE NOT NULL,
    User_type         VARCHAR(20) NOT NULL
                          CHECK (User_type IN ('agent','prospective_renter'))
);

-- 2. Agent (inherits via 1:1 to Users)
CREATE TABLE Agent (
    Agent_ID             SERIAL PRIMARY KEY,
    User_ID              INT UNIQUE NOT NULL
                           REFERENCES Users(User_ID) ON DELETE CASCADE,
    Job_title            VARCHAR(250),
    Agency_name          VARCHAR(250),
    Contract_type        VARCHAR(50),
    --Contract_start_date  DATE,
    --Contract_end_date    DATE,
    --Salary               DECIMAL(10,2),
    --Commission           DECIMAL(10,2),
    CONSTRAINT chk_contract_dates
      CHECK (
        Contract_start_date IS NULL
        OR Contract_end_date IS NULL
        OR Contract_end_date > Contract_start_date
      )
);

-- 3. Prospective Renter (inherits via 1:1 to Users)
CREATE TABLE Prospective_renter (
    Renter_ID           SERIAL PRIMARY KEY,
    User_ID             INT UNIQUE NOT NULL
                           REFERENCES Users(User_ID) ON DELETE CASCADE,
    Move_in_date        DATE,
    Preferred_location  VARCHAR(250),
    Budget              DECIMAL(10,2)
);

-- 4. Address
CREATE TABLE Address (
    Address_ID     SERIAL PRIMARY KEY,
    User_ID        INT NOT NULL
                      REFERENCES Users(User_ID) ON DELETE CASCADE,
    Street         VARCHAR(250) NOT NULL,
    City           VARCHAR(250) NOT NULL,
    State          VARCHAR(250),
    Zip_code       VARCHAR(10),
    Country        VARCHAR(250),
    Address_type   VARCHAR(10) NOT NULL
                      CHECK (Address_type IN ('primary','payment'))
);

-- 5. Credit Card
CREATE TABLE Credit_card (
    Card_ID             SERIAL PRIMARY KEY,
    Card_number         VARCHAR(20) UNIQUE NOT NULL,
    Renter_ID           INT NOT NULL
                           REFERENCES Prospective_renter(Renter_ID) ON DELETE CASCADE,
    Expiry_date         DATE NOT NULL,
    Payment_address_ID  INT NOT NULL
                           REFERENCES Address(Address_ID) ON DELETE RESTRICT
);

-- 6. Neighborhood (needed before Property)
CREATE TABLE Neighborhood (
    Neighborhood_ID      SERIAL PRIMARY KEY,
    Neighborhood_name    VARCHAR(250) NOT NULL,
    Crime_rate           DECIMAL(5,2),
    School_rating        INT,
    Has_vacation_home    BOOLEAN,
    Has_land_available   BOOLEAN,
    Amenities_available  BOOLEAN
);

-- 7. Property
CREATE TABLE Property (
    Property_ID        SERIAL PRIMARY KEY,
    Address_ID         INT NOT NULL
                          REFERENCES Address(Address_ID) ON DELETE CASCADE,
    Agent_ID           INT NOT NULL
                          REFERENCES Agent(Agent_ID) ON DELETE RESTRICT,
    Neighborhood_ID    INT
                          REFERENCES Neighborhood(Neighborhood_ID)
                          ON DELETE SET NULL,
    Type               VARCHAR(20) NOT NULL
                          CHECK (Type IN ('house','apartment','commercial')),
    Number_of_rooms    INT,
    Square_footage     DECIMAL(10,2),
    Agency_name        VARCHAR(250),
    Type_of_business   VARCHAR(250),
    Availability       BOOLEAN NOT NULL
);

-- 8. Property Features
CREATE TABLE Property_features (
    Property_ID           INT PRIMARY KEY
                              REFERENCES Property(Property_ID) ON DELETE CASCADE,
    Has_vacation_home     BOOLEAN DEFAULT FALSE,
    Has_land_available    BOOLEAN DEFAULT FALSE,
    Amenities_available   BOOLEAN DEFAULT FALSE
);

-- 9. Price History
CREATE TABLE Price (
    Price_ID        SERIAL PRIMARY KEY,
    Property_ID     INT NOT NULL
                         REFERENCES Property(Property_ID) ON DELETE CASCADE,
    Rental_price    DECIMAL(10,2) NOT NULL,
    Effective_date  DATE DEFAULT CURRENT_DATE,
    CONSTRAINT uq_price_per_day
      UNIQUE (Property_ID, Effective_date)
);

-- 10. Booking
CREATE TABLE Booking (
    Booking_ID     SERIAL PRIMARY KEY,
    Property_ID    INT NOT NULL
                         REFERENCES Property(Property_ID) ON DELETE CASCADE,
    Renter_ID      INT NOT NULL
                         REFERENCES Prospective_renter(Renter_ID) ON DELETE CASCADE,
    Card_ID        INT NOT NULL
                         REFERENCES Credit_card(Card_ID) ON DELETE RESTRICT,
    Booking_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    Start_date     DATE NOT NULL,
    Lease_till_date DATE NOT NULL,
    CONSTRAINT chk_lease_dates
      CHECK (Lease_till_date > Start_date)
);

-- 11. Reward Program
CREATE TABLE Reward_program (
    Reward_ID     SERIAL PRIMARY KEY,
    Renter_ID     INT NOT NULL
                         REFERENCES Prospective_renter(Renter_ID) ON DELETE CASCADE,
    Booking_ID    INT NOT NULL
                         REFERENCES Booking(Booking_ID) ON DELETE CASCADE,
    Reward_points INT NOT NULL
);

-- 12. Indexes for Performance
CREATE INDEX idx_property_agent       ON Property(Agent_ID);
CREATE INDEX idx_property_neighborhood ON Property(Neighborhood_ID);
CREATE INDEX idx_price_property_id   ON Price(Property_ID);
CREATE INDEX idx_booking_renter      ON Booking(Renter_ID);
CREATE INDEX idx_booking_property    ON Booking(Property_ID);
CREATE INDEX idx_credit_card_renter  ON Credit_card(Renter_ID);
CREATE INDEX idx_credit_card_pay_addr ON Credit_card(Payment_address_ID);
