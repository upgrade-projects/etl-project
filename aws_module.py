import aioboto3 
import asyncio 
 
async def extract_aws_data(): 
    session = aioboto3.Session() 
 
    async with session.client("s3") as s3_client: 
        response = await s3_client.get_object(Bucket="your-bucket", Key="your-sample.csv") 
        content = await response["Body"].read() 
 
    await asyncio.sleep(1)  # simulate ETL work 
    return {"message": "AWS file extracted", "size": len(content)} 