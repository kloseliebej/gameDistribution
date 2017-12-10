drop table if exists users;
create table users (
  userID integer primary key autoincrement,
  name text not null,
  password text not null,
  email text not null UNIQUE ,
  isGamer integer not null,
  isDeveloper integer not null,
  isManager integer not null
);

insert into users (name, password, email, isGamer, isDeveloper, isManager) values ('manager', '123', 'm@gmail.com', 0 , 0 , 1 );

drop table if exists payment_information;
create table payment_information (
  cardID integer PRIMARY KEY,
  CVV text not null,
  expDate text not null,
  name text not null,
  userID integer not null,
  FOREIGN KEY (userID) REFERENCES users (userID)
  ON DELETE CASCADE ON UPDATE NO ACTION
);

drop table if exists bank_account;
create table bank_account (
  accountID text not null UNIQUE,
  routingID text not null UNIQUE,
  address text not null,
  name text not null,
  userID integer not null,
  isDefault integer not null,
  FOREIGN KEY (userID) REFERENCES users (userID)
  ON DELETE CASCADE ON UPDATE NO ACTION ,
  PRIMARY KEY (accountID, routingID)
);

drop table if exists games;
create table games(
  gameID integer PRIMARY KEY AUTOINCREMENT ,
  name text not null UNIQUE ,
  discount integer not null,
  price integer not null,
  developerID integer not null,
  publishDate text not null,
  FOREIGN KEY (developerID) REFERENCES users (userID)
  ON DELETE CASCADE ON UPDATE NO ACTION
);

drop table if exists reviews;
create table reviews (
  reviewID integer PRIMARY KEY AUTOINCREMENT ,
  rating integer not null,
  comment text not null,
  userID integer not null,
  gameID integer not null,
  FOREIGN KEY (userID) REFERENCES users (userID)
  ON DELETE SET NULL ON UPDATE NO ACTION ,
  FOREIGN KEY (gameID) REFERENCES games (gameID)
  ON DELETE CASCADE ON UPDATE NO ACTION
);

drop table if exists genres;
create table genres (
  genre text not null,
  gameID integer not null,
  FOREIGN KEY (gameID) REFERENCES games (gameID)
  ON DELETE CASCADE ON UPDATE NO ACTION ,
  PRIMARY KEY (genre, gameID)
);

drop table if exists transactions;
create table transactions (
  date text not null,
  gameID integer not null,
  userID integer not null,
  FOREIGN KEY (gameID) REFERENCES games (gameID)
  ON DELETE SET NULL ON UPDATE NO ACTION ,
  FOREIGN KEY (userID) REFERENCES users (userID)
  ON DELETE SET NULL ON UPDATE NO ACTION ,
  PRIMARY KEY (gameID, userID)
);