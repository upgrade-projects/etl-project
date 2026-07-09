from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import pandas as pd
import sqlite3
import uuid
from typing import List, Dict, Optional
import gcsfs 
import asyncio 
from azure.storage.blob.aio import BlobServiceClient 
import aioboto3 
from pydantic import BaseModel, Field
import os
from io import BytesIO

app = FastAPI(title="ETL API", version="1.0")

# In-memory storage for datasets
data_store = {}

DATABASE = "etl.db"
class PersonRecord(BaseModel):
    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=18, le=100)
    city: str = Field(..., min_length=1)
    salary: float = Field(..., ge=0)

def validate_records(df):
    valid_rows = []
    errors = []
    for index, row in df.iterrows():
        try:
            record = PersonRecord(**row.to_dict())
            valid_rows.append(record.dict())
        except Exception as e:
            errors.append({"row": index, "error": str(e)})
    return valid_rows, errors



# Helper function to retrieve dataframe
def get_dataframe(token: str):
    if token not in data_store:
        raise HTTPException(status_code=400, detail="Invalid token")
    return data_store[token]


# -------------------------
# Extract CSV API
# -------------------------
@app.post("/extract-csv")
async def extract_csv(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(pd.io.common.BytesIO(contents))

    token = str(uuid.uuid4())
    data_store[token] = df

    return {
        "token": token,
        "preview": df.head().to_dict(orient="records"),
    }


# -------------------------
# Extract JSON API
# -------------------------
class JSONInput(BaseModel):
    records: List[Dict]


@app.post("/extract-json")
def extract_json(payload: JSONInput):
    df = pd.DataFrame(payload.records)

    token = str(uuid.uuid4())
    data_store[token] = df

    return {
        "token": token,
        "preview": df.head().to_dict(orient="records"),
    }

# -------------------------
# Extract Validated CSV
# -------------------------
@app.post("/extract-csv-validated")
async def extract_csv_validated(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(pd.io.common.BytesIO(contents))
    valid_rows, errors = validate_records(df)
    if len(valid_rows) == 0:
        return {"message": "No valid rows after validation", "errors":errors}
    clean_df = pd.DataFrame(valid_rows)
    token = str(uuid.uuid4())
    data_store[token] = clean_df
    return {
    "token": token,
    "preview": clean_df.head().to_dict(orient="records"),
    "errors": errors
    }

# Async endpoint to read file from GCS 
@app.get("/extract-gcp") 
async def extract_data_from_gcp(): 
    # Connect to GCS (ensure your GCP credentials are available) 
    fs = gcsfs.GCSFileSystem(
    token=r"gcp.json"
    )

    print(fs.ls("upgrad-etl-bucket"))
    #fs = gcsfs.GCSFileSystem( project="upgrad-project-501417") 
    def load_csv():
        with fs.open("upgrad-etl-bucket/sample.csv", "rb") as f: 
            return pd.read_csv(f)
    df=await asyncio.to_thread(load_csv)
 
    return { 
        "message": "File extracted successfully", 
        "columns":list(df.columns),
        "preview" :df.head().to_dict(orient="records")
    } 

# # Create async blob client 
# blob_service_client = BlobServiceClient.from_connection_string("your-azure-conn-string") 
 
# @app.get("/extract-from-azure") 
# async def extract_from_azure(): 
#     # 1. Connect to container + blob 
#     container_client = blob_service_client.get_container_client("your-container-name") 
#     blob_client = container_client.get_blob_client("your-blob-name.csv") 
 
#     # 2. Download blob asynchronously 
#     stream = await blob_client.download_blob() 
#     content = await stream.readall() 
 
#     # 3. Simulate async ETL work 
#     await asyncio.sleep(1) 
 
#     # 4. Return response 
#     return { 
#         "message": "Azure blob extracted successfully", 
#         "size": len(content) 
#     }

@app.get("/extract-s3") 
async def extract_from_s3():
    session = aioboto3.Session() 
 
    # Create async S3 client 
    async with session.client("s3",region_name="ap-south-1") as s3_client: 
        # Download file asynchronously 
        response = await s3_client.get_object( 
             Bucket="upgrad-etl-s3-bucket", 
             Key="sample.csv" 
        ) 
        content = await response["Body"].read() 
         # Read CSV into a DataFrame
        df = pd.read_csv(BytesIO(content))
        # Simulate ETL processing 
        await asyncio.sleep(1) 
 
        return { 
           "message": "File extracted from S3",
            "size_in_bytes": len(content),
            "rows": len(df),
            "columns": list(df.columns),
            "data": df.to_dict(orient="records")
        }
  
# @app.get("/run-all") 
# async def run_all_extractors(): 
#     results = await asyncio.gather( 
#         extract_gcp_data(), 
#         extract_azure_data(), 
#         extract_aws_data() 
#     ) 
#     return { 
#         "GCP": results[0], 
#         "Azure": results[1], 
#         "AWS": results[2] 
#     } 
# -------------------------
# Transform API
# -------------------------
class FilterCondition(BaseModel):
    column: str
    operator: str
    value: str


class TransformInstruction(BaseModel):
    token: str
    select: Optional[List[str]] = None
    rename: Optional[Dict[str, str]] = None
    filters: Optional[List[FilterCondition]] = None


@app.post("/transform")
def transform_data(instruction: TransformInstruction):
    df = get_dataframe(instruction.token).copy()

    # Column selection
    if instruction.select:
        df = df[instruction.select]

    # Rename columns
    if instruction.rename:
        df = df.rename(columns=instruction.rename)

    # Apply filters
    if instruction.filters:
        for f in instruction.filters:
            if f.operator == ">":
                df = df[df[f.column] > float(f.value)]

            elif f.operator == "<":
                df = df[df[f.column] < float(f.value)]

            elif f.operator == "contains":
                df = df[df[f.column].str.contains(f.value, case=False)]

    data_store[instruction.token] = df

    return {
        "message": "Transformation applied",
        "data": df.to_dict(orient="records"),
    }


# -------------------------
# Load API
# -------------------------
class LoadRequest(BaseModel):
    token: str
    table_name: str = "etl_table"


@app.post("/load")
def load_to_sqlite(request: LoadRequest):
    df = get_dataframe(request.token)
    conn = sqlite3.connect(DATABASE)
    df.to_sql(request.table_name, conn, if_exists="replace", index=False)
    conn.close()

    return {
        "status": "Data loaded successfully",
    }