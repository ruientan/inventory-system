DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    location_id INTEGER NOT NULL,
    role TEXT CHECK(role IN ('HQ', 'Mbella', 'Citibella')) NOT NULL DEFAULT 'HQ'
);

INSERT INTO users (user_id, username, password_hash, location_id, role) VALUES
(1, 'HQ', 'scrypt:32768:8:1$72Hg5MpHXvMwzTsn$62a10b5a52ed794b569a6f9e11191c0a4233385a110fe7b3ce6da4c4e0b47a0d9376733e775e49114f5311e0c10c0949c55515bc5da9b447d67edaa20ba37aaa', 1, 'HQ'),
(2, 'Mbella', 'scrypt:32768:8:1$UzGKbS2o9aCZIS4e$3cab652e0ff2a1bac30e9c5ff68006594438d600d9ca84f193a210525110268fb540e3f3614c2c27600a40828d339b59b04a30c3f82f0e48b53d16294434fd87', 2, 'Mbella'),
(3, 'Citibella', 'scrypt:32768:8:1$Sigqo2cdU5hnRlBX$565f58ca82820609d0ef4ed94900754a1de1c8a2d62441f9f5a3833733f6e8b255d56f322b98df9c9423f1d9ebbc61afe1fe1a9ebdda3ff62138ffb270c70ee9', 3, 'Citibella');
