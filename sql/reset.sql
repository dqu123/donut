/*
 * This script resets the test database to a consistent state
 * and should be run at the beginning of each integration test.
 */

DROP DATABASE IF EXISTS donut_test;
CREATE DATABASE donut_test;
USE donut_test;

-- Create the database schema.
SOURCE sql/donut.sql

-- Populate with test data.
SOURCE sql/test_data.sql