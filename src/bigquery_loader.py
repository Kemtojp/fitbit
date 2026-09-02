import os
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# 1. Rutas y configuración
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
KEY_PATH = os.path.join(BASE_DIR, "credentials.json")

PROJECT_ID = "fitbit-506223"
DATASET_ID = "fitbit_clean_data"

def upload_to_bigquery():
    print("Conectando con Google Cloud BigQuery...")
    
    # 2. Autenticación con el archivo JSON
    if not os.path.exists(KEY_PATH):
        raise FileNotFoundError(f"No se encontró el archivo {KEY_PATH}. Revisa el Paso 1.")
    
    credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
    client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

    # 3. Mapeo de archivos Parquet a tablas de BigQuery
    tables_to_upload = {
        "daily_summary": "daily_summary.parquet",
        "hourly_summary": "hourly_summary.parquet",
        "weight_summary": "weight_summary.parquet"
    }

    # 4. Carga de cada tabla
    for table_name, parquet_file in tables_to_upload.items():
        file_path = os.path.join(PROCESSED_DIR, parquet_file)
        
        if not os.path.exists(file_path):
            print(f"Saltando {table_name}: no se encontró {file_path}")
            continue
            
        print(f"Leyendo {parquet_file}...")
        df = pd.read_parquet(file_path)

        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",  # Reemplaza la tabla si ya existe
            autodetect=True
        )

        print(f"Subiendo {len(df)} registros a la tabla '{table_id}'...")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Espera a que termine el trabajo en la nube

        print(f"Tabla '{table_name}' cargada exitosamente.")

    print("\nTodas las tablas limpias han sido publicadas en BigQuery.")

if __name__ == "__main__":
    upload_to_bigquery()