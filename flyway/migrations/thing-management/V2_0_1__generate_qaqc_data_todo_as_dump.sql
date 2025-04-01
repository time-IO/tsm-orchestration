-- ===========================================
-- Migration: Insert Realistic Test Data for QA/QC
-- ===========================================
-- NOTE: This test data assumes:
-- - A single project exists with `project_id = 1`
-- - A single user exists with `created_by = 1`
-- ===========================================

-- Insert QA/QC Settings and commit
INSERT INTO "qaqc_setting" ("uuid", "name", "context_window", "project_id", "created_by", "created_at")
VALUES
    ('550e8400-e29b-41d4-a716-446655440000', 'Temperature Monitoring', '30 min', 1, 1, NOW()),
    ('550e8400-e29b-41d4-a716-446655440001', 'Sensor Accuracy Check', '15 min', 1, 1, NOW()),
    ('550e8400-e29b-41d4-a716-446655440002', 'Anomaly Detection', '1 hour', 1, 1, NOW()),
    ('550e8400-e29b-41d4-a716-446655440003', 'Humidity Control', '45 min', 1, 1, NOW()),
    ('550e8400-e29b-41d4-a716-446655440004', 'Pressure Stability', '20 min', 1, 1, NOW());

COMMIT;

-- Insert Functions and commit
INSERT INTO "function" ("name", "description", "created_by", "created_at")
VALUES
    ('Temperature Range Check', 'Ensures sensor temperature remains within an acceptable range.', 1, NOW()),
    ('Outlier Detection', 'Identifies sensor readings that deviate significantly from the expected range.', 1, NOW()),
    ('Drift Monitoring', 'Monitors sensor data for gradual deviations over time.', 1, NOW()),
    ('Humidity Variation Check', 'Checks for rapid fluctuations in humidity levels.', 1, NOW()),
    ('Pressure Threshold Alert', 'Triggers an alert if pressure exceeds or drops below a defined threshold.', 1, NOW());

COMMIT;

-- Insert Function Parameters using dynamic function IDs
INSERT INTO "function_parameter" ("function_id", "name", "description", "optional", "type", "default_value", "position")
VALUES
    ((SELECT id FROM "function" WHERE name = 'Temperature Range Check'), 'min_temperature', 'Minimum allowed temperature (°C)', FALSE, 'float', '0.0', 1),
    ((SELECT id FROM "function" WHERE name = 'Temperature Range Check'), 'max_temperature', 'Maximum allowed temperature (°C)', FALSE, 'float', '50.0', 2),
    ((SELECT id FROM "function" WHERE name = 'Outlier Detection'), 'sensitivity', 'Sensitivity threshold for outlier detection', FALSE, 'float', '2.5', 1),
    ((SELECT id FROM "function" WHERE name = 'Drift Monitoring'), 'drift_limit', 'Maximum allowable drift before triggering alert', FALSE, 'float', '1.0', 1),
    ((SELECT id FROM "function" WHERE name = 'Humidity Variation Check'), 'max_humidity_change', 'Maximum humidity variation allowed within the context window', FALSE, 'float', '5.0', 1),
    ((SELECT id FROM "function" WHERE name = 'Pressure Threshold Alert'), 'min_pressure', 'Minimum pressure allowed (bar)', FALSE, 'float', '1.0', 1),
    ((SELECT id FROM "function" WHERE name = 'Pressure Threshold Alert'), 'max_pressure', 'Maximum pressure allowed (bar)', FALSE, 'float', '3.5', 2);

COMMIT;

-- Link Functions to QA/QC Settings
INSERT INTO "qaqc_setting_function" ("qaqc_setting_id", "function_id", "name", "position")
VALUES
    ((SELECT id FROM "qaqc_setting" WHERE name = 'Temperature Monitoring'), (SELECT id FROM "function" WHERE name = 'Temperature Range Check'), 'Temperature Range Check', 1),
    ((SELECT id FROM "qaqc_setting" WHERE name = 'Temperature Monitoring'), (SELECT id FROM "function" WHERE name = 'Outlier Detection'), 'Outlier Detection', 2),
    ((SELECT id FROM "qaqc_setting" WHERE name = 'Sensor Accuracy Check'), (SELECT id FROM "function" WHERE name = 'Outlier Detection'), 'Outlier Detection', 1),
    ((SELECT id FROM "qaqc_setting" WHERE name = 'Sensor Accuracy Check'), (SELECT id FROM "function" WHERE name = 'Drift Monitoring'), 'Drift Monitoring', 2),
    ((SELECT id FROM "qaqc_setting" WHERE name = 'Anomaly Detection'), (SELECT id FROM "function" WHERE name = 'Outlier Detection'), 'Outlier Detection', 1),
    ((SELECT id FROM "qaqc_setting" WHERE name = 'Anomaly Detection'), (SELECT id FROM "function" WHERE name = 'Drift Monitoring'), 'Drift Monitoring', 2),
    ((SELECT id FROM "qaqc_setting" WHERE name = 'Humidity Control'), (SELECT id FROM "function" WHERE name = 'Humidity Variation Check'), 'Humidity Variation Check', 1),
    ((SELECT id FROM "qaqc_setting" WHERE name = 'Pressure Stability'), (SELECT id FROM "function" WHERE name = 'Pressure Threshold Alert'), 'Pressure Threshold Alert', 1);

COMMIT;

-- Link Function Parameters to QA/QC Settings
INSERT INTO "qaqc_setting_function_parameter" ("qaqc_setting_function_id", "function_parameter_id", "value")
VALUES
    ((SELECT id FROM "qaqc_setting_function" WHERE qaqc_setting_id = (SELECT id FROM "qaqc_setting" WHERE name = 'Temperature Monitoring')
        AND function_id = (SELECT id FROM "function" WHERE name = 'Temperature Range Check')),
     (SELECT id FROM "function_parameter" WHERE name = 'min_temperature'), '-5.0'),

    ((SELECT id FROM "qaqc_setting_function" WHERE qaqc_setting_id = (SELECT id FROM "qaqc_setting" WHERE name = 'Temperature Monitoring')
        AND function_id = (SELECT id FROM "function" WHERE name = 'Temperature Range Check')),
     (SELECT id FROM "function_parameter" WHERE name = 'max_temperature'), '40.0'),

    ((SELECT id FROM "qaqc_setting_function" WHERE qaqc_setting_id = (SELECT id FROM "qaqc_setting" WHERE name = 'Sensor Accuracy Check')
        AND function_id = (SELECT id FROM "function" WHERE name = 'Outlier Detection')),
     (SELECT id FROM "function_parameter" WHERE name = 'sensitivity'), '3.0'),

    ((SELECT id FROM "qaqc_setting_function" WHERE qaqc_setting_id = (SELECT id FROM "qaqc_setting" WHERE name = 'Sensor Accuracy Check')
        AND function_id = (SELECT id FROM "function" WHERE name = 'Drift Monitoring')),
     (SELECT id FROM "function_parameter" WHERE name = 'drift_limit'), '0.5');

COMMIT;
