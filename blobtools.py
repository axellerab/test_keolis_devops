from azure.storage.blob import BlobServiceClient

def connect_blob(connect_str):
    # Create the BlobServiceClient object which will be used to create a container client
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    return blob_service_client

def create_or_update_container(blob_service_client, container_name):
    # Create a unique name for the container
    try:
        # Create the container
        container_client = blob_service_client.create_container(container_name)
    except Exception as ex:
        print('Exception:')
        print(ex)
    return container_name

def upload_file_to_blob(blob_service_client, local_path, container_name, file_name):
    # Create a path in local Documents directory to upload
    upload_file_path = local_path
    # Create a blob client using the local file name as the name for the blob
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)

    # Upload the created file
    with open(upload_file_path, "rb") as data:
        blob_client.upload_blob(data)
    return local_path, container_name, file_name

