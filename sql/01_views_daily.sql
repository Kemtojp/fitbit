CREATE OR REPLACE VIEW `fitbit-506223.fitbit_clean_data.view_daily_kpis` AS
SELECT
    Id,
    ActivityDate,
    FORMAT_DATE('%A', ActivityDate) AS DayOfWeek,
    FORMAT_DATE('%u', ActivityDate) AS DayOfWeekNumber,
    CASE 
        WHEN FORMAT_DATE('%u', ActivityDate) IN ('6', '7') THEN 'Fin de semana'
        ELSE 'Día de semana'
    END AS PartOfWeek,
    TotalSteps,
    TotalDistance,
    Calories,
    VeryActiveMinutes,
    FairlyActiveMinutes,
    LightlyActiveMinutes,
    SedentaryMinutes,
    (VeryActiveMinutes + FairlyActiveMinutes + LightlyActiveMinutes) AS TotalActiveMinutes,
    UserType,
    TotalMinutesAsleep,
    TotalTimeInBed,
    MinutesAwakeInBed,
    ROUND(TotalMinutesAsleep / 60.0, 2) AS HoursAsleep,
    CASE
        WHEN TotalMinutesAsleep IS NULL THEN 'Sin registro'
        WHEN TotalMinutesAsleep < 420 THEN 'Menos de 7h'
        WHEN TotalMinutesAsleep BETWEEN 420 AND 540 THEN '7h - 9h (Óptimo)'
        ELSE 'Más de 9h'
    END AS SleepCategory
FROM `fitbit-506223.fitbit_clean_data.daily_summary`;