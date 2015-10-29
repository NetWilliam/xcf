DROP DATABASE IF EXISTS xcf;
CREATE DATABASE xcf DEFAULT charset utf8 COLLATE utf8_general_ci;
USE xcf;

CREATE TABLE profile (
    profile_id int primary key auto_increment,
    profile_bind_cnt int not null default 0,
    profile_username varchar(128) not null,
    profile_welcome text
)auto_increment=1000;

CREATE TABLE local_auth (
    local_auth_id int primary key auto_increment,
    local_auth_profile_id int not null,
    local_auth_password varchar(128) not null
)auto_increment=1000;

CREATE TABLE oauth (
    oauth_id int primary key auto_increment,
    oauth_profile_id int default 0,
    oauth_from varchar(16) not null,
    oauth_access_token varchar(128) default '',
    oauth_server_user_id varchar(128) not null,
    oauth_expires int not null
)auto_increment=1000;

CREATE TABLE api_oauth (
    api_oauth_id int primary key auto_increment,
    api_oauth_profile_id int not null,
    api_oauth_api_key varchar(128),
    api_oauth_api_secret varchar(128)
)auto_increment=1000;

