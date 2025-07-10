DROP TABLE IF EXISTS locations;

CREATE TABLE locations (
  location_id SERIAL PRIMARY KEY,
  name TEXT
);

INSERT INTO locations (location_id, name) VALUES
(1, 'HQ'),
(2, 'Mbella'),
(3, 'Citibella');
