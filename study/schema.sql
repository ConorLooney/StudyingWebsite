DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS deck;
DROP TABLE IF EXISTS term;
DROP TABLE IF EXISTS routine;
DROP TABLE IF EXISTS save_deck;
DROP TABLE IF EXISTS save_routine;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE deck (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_public BIT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user (id)
);

CREATE TABLE term (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deck_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    FOREIGN KEY (deck_id) REFERENCES deck (id)
);

CREATE TABLE routine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    steps TEXT NOT NULL,
    is_public BIT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user (id)
);

CREATE TABLE save_deck (
    user_id INTEGER NOT NULL,
    deck_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (deck_id) REFERENCES deck (id) 
);

CREATE TABLE save_routine (
    user_id INTEGER NOT NULL,
    routine_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (routine_id) REFERENCES routine (id)
);

CREATE TABLE class (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user (id)
);

CREATE TABLE class_member (
    user_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (class_id) REFERENCES class (id)
);