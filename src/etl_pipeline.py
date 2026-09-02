import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, to_date, to_timestamp, when, round as spark_round, expr
)

def create_spark_session(app_name: str = "Bellabeat_ETL_Pipeline") -> SparkSession:
    """Inicializa y configura la sesión de Spark."""
    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark

def run_etl():
    # 1. Definir rutas relativas
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    processed_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    spark = create_spark_session()
    print("Iniciando Pipeline ETL con Apache Spark...")

    # 2. Ingesta de datos (Extract)
    print("Leyendo archivos CSV brutos...")
    df_activity_raw = spark.read.csv(os.path.join(raw_dir, "dailyActivity_merged.csv"), header=True, inferSchema=True)
    df_sleep_raw = spark.read.csv(os.path.join(raw_dir, "sleepDay_merged.csv"), header=True, inferSchema=True)
    df_hourly_intensities_raw = spark.read.csv(os.path.join(raw_dir, "hourlyIntensities_merged.csv"), header=True, inferSchema=True)
    df_hourly_steps_raw = spark.read.csv(os.path.join(raw_dir, "hourlySteps_merged.csv"), header=True, inferSchema=True)
    df_weight_raw = spark.read.csv(os.path.join(raw_dir, "weightLogInfo_merged.csv"), header=True, inferSchema=True)

    # 3. Transformación: Actividad Diaria
    print("Procesando Actividad Diaria...")
    activity_clean = df_activity_raw \
        .withColumn("ActivityDate", to_date(col("ActivityDate"), "M/d/yyyy")) \
        .dropDuplicates(["Id", "ActivityDate"])

    # 4. Transformación: Sueño Diario
    print("Procesando Sueño Diario...")
    sleep_clean = df_sleep_raw \
        .withColumn("SleepTimestamp", to_timestamp(col("SleepDay"), "M/d/yyyy h:mm:ss a")) \
        .withColumn("SleepDate", to_date(col("SleepTimestamp"))) \
        .dropDuplicates(["Id", "SleepDate"])

    # 5. Transformación e Integración Diaria (Activity + Sleep)
    print("Realizando unión de métricas diarias...")
    daily_unified = activity_clean.join(
        sleep_clean.select("Id", "SleepDate", "TotalSleepRecords", "TotalMinutesAsleep", "TotalTimeInBed"),
        (activity_clean.Id == sleep_clean.Id) & (activity_clean.ActivityDate == sleep_clean.SleepDate),
        how="left"
    ).drop(sleep_clean.Id).drop(sleep_clean.SleepDate)

    # Métricas calculadas para análisis de negocio
    daily_unified = daily_unified \
        .withColumn("MinutesAwakeInBed", 
                    when(col("TotalTimeInBed").isNotNull() & col("TotalMinutesAsleep").isNotNull(),
                         col("TotalTimeInBed") - col("TotalMinutesAsleep")).otherwise(None)) \
        .withColumn("UserType",
                    when(col("TotalSteps") < 5000, "Sedentario")
                    .when((col("TotalSteps") >= 5000) & (col("TotalSteps") < 7500), "Baja Actividad")
                    .when((col("TotalSteps") >= 7500) & (col("TotalSteps") < 10000), "Activo Moderado")
                    .otherwise("Muy Activo"))

    # 6. Transformación: Pasos e Intensidades Horarias
    print("Procesando e integrando datos horarios...")
    hourly_intensities_clean = df_hourly_intensities_raw \
        .withColumn("ActivityDateTime", to_timestamp(col("ActivityHour"), "M/d/yyyy h:mm:ss a")) \
        .withColumn("Hour", expr("hour(ActivityDateTime)")) \
        .dropDuplicates(["Id", "ActivityDateTime"])

    hourly_steps_clean = df_hourly_steps_raw \
        .withColumn("ActivityDateTime", to_timestamp(col("ActivityHour"), "M/d/yyyy h:mm:ss a")) \
        .dropDuplicates(["Id", "ActivityDateTime"])

    hourly_unified = hourly_intensities_clean.join(
        hourly_steps_clean.select("Id", "ActivityDateTime", "StepTotal"),
        on=["Id", "ActivityDateTime"],
        how="inner"
    )

    # 7. Transformación: Registro de Peso
    print("Procesando Peso y Composición Corporal...")
    weight_clean = df_weight_raw \
        .withColumn("LogDateTime", to_timestamp(col("Date"), "M/d/yyyy h:mm:ss a")) \
        .withColumn("LogDate", to_date(col("LogDateTime"))) \
        .withColumn("BMI_Rounded", spark_round(col("BMI"), 2)) \
        .dropDuplicates(["Id", "LogDateTime"])

# 8. Carga / Exportación (Load a Parquet usando motor nativo de Python)
    print(" Guardando tablas limpias en formato Parquet...")
    
    # Convertimos los DataFrames procesados por Spark a Pandas
    pdf_daily = daily_unified.toPandas()
    pdf_hourly = hourly_unified.toPandas()
    pdf_weight = weight_clean.toPandas()
    
    # Guardamos en Parquet directamente con Pandas/PyArrow
    pdf_daily.to_parquet(os.path.join(processed_dir, "daily_summary.parquet"), index=False)
    pdf_hourly.to_parquet(os.path.join(processed_dir, "hourly_summary.parquet"), index=False)
    pdf_weight.to_parquet(os.path.join(processed_dir, "weight_summary.parquet"), index=False)

    print("\n Pipeline ETL finalizado con éxito.")
    print(f"Registros diarios procesados: {len(pdf_daily)}")
    print(f"Registros horarios procesados: {len(pdf_hourly)}")
    print(f"Registros de peso procesados: {len(pdf_weight)}")

    spark.stop()

if __name__ == "__main__":
    run_etl()