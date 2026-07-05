import gcsfs 
import asyncio 
 
async def extract_gcp_data(): 
    fs = gcsfs.GCSFileSystem(project="your-gcp-project-id") 
 
    async with fs.open("your-bucket-name/your-sample.csv", "r") as f: 
        content = await f.read() 
 
    await asyncio.sleep(1)  # simulate ETL work 
    return {"message": "GCP file extracted", "size": len(content)} 