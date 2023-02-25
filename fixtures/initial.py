CREATE_TABLES_SQL = """CREATE TABLE "user_role" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(10) NOT NULL UNIQUE);
CREATE TABLE "user" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "username" varchar(255) NOT NULL UNIQUE,
    "first_name" varchar(255) NOT NULL,
    "telegram_id" integer NOT NULL UNIQUE,
    "language_code" varchar(2) NOT NULL,
    "time_added" datetime NOT NULL,
    "role_id" bigint NOT NULL REFERENCES "user_role" ("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE "user_message" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "text" TEXT NOT NULL,
    "message_id" integer NOT NULL,
    "time_added" datetime NOT NULL,
    "user_id" bigint NOT NULL REFERENCES "user" ("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX "user_role_id_c3a87a3d" ON "user" ("role_id");
CREATE INDEX "user_message_user_id_8a912feb" ON "user_message" ("user_id");
INSERT INTO `user_role` (`id`, `name`) VALUES
    (1, 'admin'),
    (2, 'client'),
    (3, 'alient'),
    (4, 'blocked');"""