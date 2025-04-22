-- ===========================================
-- Migration: Allow multiple same functions per QAQC setting
-- ===========================================

-- Drop the unique constraint from qaqc_setting_function
ALTER TABLE "qaqc_setting_function"
    DROP CONSTRAINT IF EXISTS "qaqc_setting_function_qaqc_setting_id_function_id_key";