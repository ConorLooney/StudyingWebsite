DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS deck;
DROP TABLE IF EXISTS term;
DROP TABLE IF EXISTS routine;
DROP TABLE IF EXISTS class;
DROP TABLE IF EXISTS invite_code;
DROP TABLE IF EXISTS save_deck;
DROP TABLE IF EXISTS save_routine;
DROP TABLE IF EXISTS deck_class;
DROP TABLE IF EXISTS routine_class;
DROP TABLE IF EXISTS user_class; 
DROP TABLE IF EXISTS admin_class;
DROP TABLE IF EXISTS join_request;
DROP TABLE IF EXISTS folder;
DROP TABLE IF EXISTS attempt;
DROP TABLE IF EXISTS study_session;
DROP TABLE IF EXISTS spaced_repetition;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE deck (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    folder_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_public BIT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user (id),
    FOREIGN KEY (folder_id) REFERENCES folder (id)
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
    folder_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (deck_id) REFERENCES deck (id),
    FOREIGN KEY (folder_id) REFERENCES folder (id),
    UNIQUE(user_id, deck_id)
);

CREATE TABLE save_routine (
    user_id INTEGER NOT NULL,
    routine_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (routine_id) REFERENCES routine (id),
    UNIQUE(user_id, routine_id)
);

CREATE TABLE class (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL, 
    is_public BIT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user (id)
);

CREATE TABLE user_class (
    user_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (class_id) REFERENCES class (id),
    UNIQUE(user_id, class_id)
);

CREATE TABLE deck_class (
    deck_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    FOREIGN KEY (deck_id) REFERENCES deck (id),
    FOREIGN KEY (class_id) REFERENCES class (id),
    UNIQUE(deck_id, class_id)
);

CREATE TABLE routine_class (
    routine_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    FOREIGN KEY (routine_id) REFERENCES routine (id),
    FOREIGN KEY (class_id) REFERENCES class (id),
    UNIQUE(routine_id, class_Id)
);

CREATE TABLE admin_class (
    admin_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    FOREIGN KEY (admin_id) REFERENCES user (id),
    FOREIGN KEY (class_id) REFERENCES class (id),
    UNIQUE(admin_id, class_id)
);

CREATE TABLE join_request (
    requester_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    FOREIGN KEY (requester_id) REFERENCES user (id),
    FOREIGN KEY (class_id) REFERENCES class (id),
    UNIQUE (requester_id, class_id)
);

CREATE TABLE invite_code (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    code TEXT UNIQUE NOT NULL,
    class_id INTEGER NOT NULL,
    FOREIGN KEY (class_id) REFERENCES class (id),
    UNIQUE(class_id)
);

CREATE TABLE folder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    owner_id INTEGER NOT NULL,
    parent_id INTEGER NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user (id),
    FOREIGN KEY (parent_id) REFERENCES folder (id)
);

CREATE TABLE attempt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    step TEXT NOT NULL,
    is_correct BIT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    term_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (term_id) REFERENCES term (id),
    FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE study_session (
    user_id INTEGER NOT NULL,
    routine_id INTEGER NOT NULL,
    date_studied TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (routine_id) REFERENCES routine (id),
    PRIMARY KEY (user_id, routine_id)
);

CREATE TABLE spaced_repetition (
    user_id INTEGER NOT NULL,
    deck_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (deck_id) REFERENCES deck (id),
    PRIMARY KEY (user_id, deck_id)
);