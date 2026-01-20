
SET FOREIGN_KEY_CHECKS = 0;

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

SET FOREIGN_KEY_CHECKS = 1;

-- Table: schools (NEW)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: course (Linked to School)
CREATE TABLE `course` (
  `course_id` int NOT NULL AUTO_INCREMENT,
  `course_name` varchar(20) NOT NULL,
  `school_id` int NOT NULL,
  PRIMARY KEY (`course_id`),
  FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: class (Linked to School)
CREATE TABLE `class` (
  `class_id` int NOT NULL AUTO_INCREMENT,
  `class_name` varchar(20) NOT NULL, 
  `school_id` int NOT NULL,
  PRIMARY KEY (`class_id`),
  FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: room (Linked to School)
CREATE TABLE `room` (
  `room_id` int NOT NULL AUTO_INCREMENT,
  `room_name` varchar(20) NOT NULL,
  `room_type` enum('practical','lecture') NOT NULL,
  `school_id` int NOT NULL,
  PRIMARY KEY (`room_id`),
  FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: teacher (Linked to School)
CREATE TABLE `teacher` (
  `teacher_id` int NOT NULL AUTO_INCREMENT,
  `teacher_name` varchar(100) NOT NULL,
  `school_id` int NOT NULL,
  PRIMARY KEY (`teacher_id`),
  FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: timeslot (Shared structure but can be filtered or just accumulated. Using simple structure)
CREATE TABLE `timeslot` (
  `time_id` int NOT NULL AUTO_INCREMENT,
  `timeslot` time NOT NULL,
  `type_of_class` enum('lecture','practical') NOT NULL,
  PRIMARY KEY (`time_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: subject (Linked to School)
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
  FOREIGN KEY (`class_id`) REFERENCES `class` (`class_id`),
  FOREIGN KEY (`course_id`) REFERENCES `course` (`course_id`),
  FOREIGN KEY (`teacher_id`) REFERENCES `teacher` (`teacher_id`),
  FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: timetable (Linked to School)
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
  FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
  FOREIGN KEY (`time_id`) REFERENCES `timeslot` (`time_id`),
  FOREIGN KEY (`teacher_id`) REFERENCES `teacher` (`teacher_id`),
  FOREIGN KEY (`subject_id`) REFERENCES `subject` (`subject_id`),
  FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
  FOREIGN KEY (`time_id`) REFERENCES `timeslot` (`time_id`),
  FOREIGN KEY (`room_id`) REFERENCES `room` (`room_id`),
  FOREIGN KEY (`class_id`) REFERENCES `class` (`class_id`),
  FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
