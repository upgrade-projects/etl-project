# etl-project

```sh
uvicorn main:app --reload
```
## Configure GCP
### Step 1: Open Google Cloud Console

1. Go to: https://console.cloud.google.com
2. create project with the name "upgrad-project"
3. Select the project that contains your Cloud Storage bucket.

### Step 2: Enable the Cloud Storage API (if not already enabled)
1. Go to APIs & Services → Library.
2. Search for Cloud Storage API.
3. Click Enable if it isn't already enabled.

### Step 3: Create Storage bucket
1. Create bucket "upgrad-etl-bucket" 
2. Upload sample.csv in the bucket.

### Step 4: Download a service account key
In the Google Cloud Console:

1. Go to IAM & Admin → Service Accounts.
2. Create or select a service account.
3. Grant it Storage Object Viewer (or a role with the necessary permissions).
4. Create a JSON key and download it; save it inside project with the name gcp.json
5. Include gcp.json in .gitignore

## Configure AWS
### Step 1: Create s3 bucket
1. Goto S3 
2. Create bucket with the name "upgrad-etl-s3-bucket"
3. Upload sample.csv into the bucket

### Step 2: Create IAM User
1. Create IAM User "upgrad-user"
2. Create custom policy with the name s3-upgrad-policy
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3FilesPermissions",
            "Effect": "Allow",
            "Action": [
                "s3files:Get*",
                "s3files:List*"
            ],
            "Resource": [
                "arn:aws:s3:::upgrad-etl-s3-bucket",
                "arn:aws:s3:::upgrad-etl-s3-bucket/*"
            ]
        }
    ]
}
```
3. Attach above policy to the user "upgrad-user"
4. Goto user, and create access key with "command line interface" option
5. Make a note of access_key_id and secret_access_key

### Step 3: Create AWS Envrionment variables
1. Create .env file
2. Mention below AWS envrionment variables (use information from previous step)
```sh
set AWS_ACCESS_KEY_ID=*******
set AWS_SECRET_ACCESS_KEY=************
set AWS_DEFAULT_REGION=<aws-region>
```
3. Include .env in .gitignore

### Step 4: Enable vscode to read from .env file

1. In vscode, Press Ctrl + , to open Settings.
2. Search for:
    Python: Terminal Use Env File
3. Enable the checkbox