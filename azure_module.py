from azure.storage.blob.aio import BlobServiceClient 
import asyncio 
 
async def extract_azure_data(): 
    blob_service_client = BlobServiceClient.from_connection_string("your-azure-conn-string") 
    container_client = blob_service_client.get_container_client("your-container-name") 
    blob_client = container_client.get_blob_client("your-sample.csv") 
 
    stream = await blob_client.download_blob() 
    content = await stream.readall() 
 
    await asyncio.sleep(1)  # simulate ETL work 
    return {"message": "Azure file extracted", "size": len(content)} 