-- Sanitize schema for Aiven MySQL 8.0
-- This script uses backticks instead of double quotes to avoid parser errors.

SET NAMES utf8mb4;
SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- Use the specific database name provided by Aiven
USE `defaultdb`;

DROP TABLE IF EXISTS `allocated_timeslots`;
DROP TABLE IF EXISTS `practical`;
DROP TABLE IF EXISTS `timetable`;
DROP TABLE IF EXISTS `subject`;
DROP TABLE IF EXISTS `teacher`;
DROP TABLE IF EXISTS `timeslot`;
DROP TABLE IF EXISTS `class`;
DROP TABLE IF EXISTS `course`;
DROP TABLE IF EXISTS `room`;
DROP TABLE IF EXISTS `schools`;

-- Table: schools
CREATE TABLE `schools` (
  `school_id` int NOT NULL AUTO_INCREMENT,
  `school_name` varchar(100) NOT NULL,
  `username` varchar(50) NOT NULL UNIQUE,
  `password_hash` varchar(255) NOT NULL,
  `start_time` varchar(10), 
  `end_time` varchar(10),
  `lecture_duration` int,
  `break_start_time` varchar(10),
  `break_duration` int,
  PRIMARY KEY (`school_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table: course
CREATE TABLE `course` (
  `course_id` int NOT NULL AUTO_INCREMENT,
  `course_name` varchar(20) NOT NULL,
  `school_id` int NOT NULL,
  PRIMARY KEY (`course_id`),
  CONSTRAINT `fk_course_school` FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table: class
CREATE TABLE `class` (
  `class_id` int NOT NULL AUTO_INCREMENT,
  `class_name` varchar(20) NOT NULL, 
  `school_id` int NOT NULL,
  PRIMARY KEY (`class_id`),
  CONSTRAINT `fk_class_school` FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table: room
CREATE TABLE `room` (
  `room_id` int NOT NULL AUTO_INCREMENT,
  `room_name` varchar(20) NOT NULL,
  `room_type` enum('practical','lecture') NOT NULL,
  `school_id` int NOT NULL,
  PRIMARY KEY (`room_id`),
  CONSTRAINT `fk_room_school` FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table: teacher
CREATE TABLE `teacher` (
  `teacher_id` int NOT NULL AUTO_INCREMENT,
  `teacher_name` varchar(100) NOT NULL,
  `school_id` int NOT NULL,
  PRIMARY KEY (`teacher_id`),
  CONSTRAINT `fk_teacher_school` FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table: timeslot
CREATE TABLE `timeslot` (
  `time_id` int NOT NULL AUTO_INCREMENT,
  `timeslot` time NOT NULL,
  `type_of_class` enum('lecture','practical') NOT NULL,
  PRIMARY KEY (`time_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table: subject
CREATE TABLE `subject` (
  `subject_id` int NOT NULL AUTO_INCREMENT,
  `subject_name` varchar(20) NOT NULL,
  `class_id` int NOT NULL,
  `course_id` int NOT NULL,
  `teacher_id` int NOT NULL,
  `semester` int NOT NULL,
  `credits` int DEFAULT 4,
  `school_id` int NOT NULL,
  PRIMARY KEY (`subject_id`),
  KEY `class_id` (`class_id`),
  KEY `course_id` (`course_id`),
  KEY `teacher_id` (`teacher_id`),
  CONSTRAINT `fk_subject_class` FOREIGN KEY (`class_id`) REFERENCES `class` (`class_id`),
  CONSTRAINT `fk_subject_course` FOREIGN KEY (`course_id`) REFERENCES `course` (`course_id`),
  CONSTRAINT `fk_subject_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `teacher` (`teacher_id`),
  CONSTRAINT `fk_subject_school` FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table: timetable
CREATE TABLE `timetable` (
  `timetable_id` int NOT NULL AUTO_INCREMENT,
  `teacher_id` int NOT NULL,
  `subject_id` int NOT NULL,
  `class_id` int NOT NULL,
  `course_id` int NOT NULL,
  `time_id` int NOT NULL,
  `day` varchar(15) DEFAULT NULL,
  `school_id` int NOT NULL,
  PRIMARY KEY (`timetable_id`),
  CONSTRAINT `fk_timetable_school` FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table: allocated_timeslots
CREATE TABLE `allocated_timeslots` (
  `allocation_id` int NOT NULL AUTO_INCREMENT,
  `teacher_id` int NOT NULL,
  `subject_id` int NOT NULL,
  `time_id` int NOT NULL,
  `school_id` int NOT NULL,
  PRIMARY KEY (`allocation_id`),
  KEY `time_id` (`time_id`),
  KEY `teacher_id` (`teacher_id`),
  KEY `subject_id` (`subject_id`),
  CONSTRAINT `fk_alloc_time` FOREIGN KEY (`time_id`) REFERENCES `timeslot` (`time_id`),
  CONSTRAINT `fk_alloc_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `teacher` (`teacher_id`),
  CONSTRAINT `fk_alloc_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`subject_id`),
  CONSTRAINT `fk_alloc_school` FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table: practical
CREATE TABLE `practical` (
  `practical_id` int NOT NULL AUTO_INCREMENT,
  `practical_name` varchar(20) NOT NULL,
  `time_id` int NOT NULL,
  `room_id` int NOT NULL,
  `class_id` int NOT NULL,
  `school_id` int NOT NULL,
  PRIMARY KEY (`practical_id`),
  KEY `time_id` (`time_id`),
  KEY `room_id` (`room_id`),
  KEY `class_id` (`class_id`),
  CONSTRAINT `fk_prac_time` FOREIGN KEY (`time_id`) REFERENCES `timeslot` (`time_id`),
  CONSTRAINT `fk_prac_room` FOREIGN KEY (`room_id`) REFERENCES `room` (`room_id`),
  CONSTRAINT `fk_prac_class` FOREIGN KEY (`class_id`) REFERENCES `class` (`class_id`),
  CONSTRAINT `fk_prac_school` FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
