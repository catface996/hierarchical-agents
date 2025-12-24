-- Migration: Add source tracking columns to execution_events table
-- Run this script to upgrade existing databases

-- Add is_global_supervisor column
ALTER TABLE execution_events
ADD COLUMN IF NOT EXISTS is_global_supervisor TINYINT(1) DEFAULT 0 COMMENT 'Is from Global Supervisor';

-- Add is_team_supervisor column
ALTER TABLE execution_events
ADD COLUMN IF NOT EXISTS is_team_supervisor TINYINT(1) DEFAULT 0 COMMENT 'Is from Team Supervisor';

-- Verify columns exist
SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'execution_events'
AND COLUMN_NAME IN ('is_global_supervisor', 'is_team_supervisor', 'team_name', 'worker_name');
