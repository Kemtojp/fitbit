CREATE OR REPLACE VIEW `fitbit-506223.fitbit_clean_data.view_hourly_trends` AS
SELECT
    Id,
    ActivityDateTime,
    Hour,
    CASE
        WHEN Hour BETWEEN 6 AND 11 THEN 'Mañana (06-11)'
        WHEN Hour BETWEEN 12 AND 17 THEN 'Tarde (12-17)'
        WHEN Hour BETWEEN 18 AND 21 THEN 'Noche (18-21)'
        ELSE 'Madrugada (22-05)'
    END AS TimeOfDay,
    TotalIntensity,
    AverageIntensity,
    StepTotal
FROM `fitbit-506223.fitbit_clean_data.hourly_summary`;