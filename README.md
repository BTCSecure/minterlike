# minterlike
PSQL Create Table

CREATE TABLE users (
    id integer NOT NULL,
    chatid bigint NOT NULL,
    address text NOT NULL,
    privatekey text NOT NULL,
    mnemo text NOT NULL,
    deeplink text NOT NULL
);
