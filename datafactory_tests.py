from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
import blobtools
import argparse

parser = argparse.ArgumentParser()
# Azure subscription ID, resource group and data factory
parser.add_argument("--subscription_id", help="SubscriptionID.", type=str)
parser.add_argument("--rg_name", help="resource group.", type=str)
parser.add_argument("--df_name", help="data factory.", type=str)
# S3 security keys
parser.add_argument("--s3_key_id", help="S3 id key.", type=str)
parser.add_argument("--s3_scrt_key", help="S3 secret key.", type=str)
# Blob keys
parser.add_argument("--blb_connect_str", help="Blob connection string.", type=str)
# Azure Credentials variables
parser.add_argument("--az_cliid", help="Azure appID/ClientID.", type=str)
parser.add_argument("--az_scrt", help="Azure secret.", type=str)
parser.add_argument("--az_tntid", help="Azure Tenant ID.", type=str)
# Data Factory Variables
# Linked services
parser.add_argument("--ls_s3_name", help="Linked service S3 Name to create.", type=str)
parser.add_argument("--ls_blob_name", help="Linked service Blob  to create.", type=str)
# Datasets
parser.add_argument("--dsin_name", help="Dataset source name to create.", type=str)
parser.add_argument("--s3_bucket", help="S3 bucket name to refer.", type=str)
parser.add_argument("--s3_path", help="S3 file or folder path to refer.", type=str)
parser.add_argument("--dsout_name", help="Dataset sink name to create.", type=str)
parser.add_argument("--blob_container_name", help="Blob container name to create.", type=str)
# Activities
parser.add_argument("--act_name", help="Activity name to create.", type=str)
# Pipeline
parser.add_argument("--pipe_name", help="Pipeline name to create.", type=str)
args = parser.parse_args()


# Specify your Active Directory client ID, client secret, and tenant ID
credentials = ServicePrincipalCredentials(client_id=args.az_cliid, secret=args.az_scrt, tenant=args.az_tntid)
adf_client = DataFactoryManagementClient(credentials, args.subscription_id)

# Create an S3 linked service
s3_scrt_key_securstr = SecureString.from_dict({'value':args.s3_scrt_key})
ls_S3storage = AmazonS3LinkedService(type='AmazonS3',access_key_id=args.s3_key_id, secret_access_key=s3_scrt_key_securstr)
adf_client.linked_services.create_or_update(args.rg_name, args.df_name, args.ls_s3_name, ls_S3storage)

# Create a Blob linked service
storage_string = SecureString(value=args.blb_connect_str)
ls_Blobstorage = AzureBlobStorageLinkedService(connection_string=storage_string)
adf_client.linked_services.create_or_update(args.rg_name, args.df_name, args.ls_blob_name, ls_Blobstorage)

# Create a S3 dataset (input)
ds_ls = LinkedServiceReference(reference_name=args.ls_s3_name)
ds_s3 = AmazonS3Dataset(linked_service_name=ds_ls, bucket_name=args.s3_bucket, key=args.s3_path)
ds = adf_client.datasets.create_or_update(args.rg_name, args.df_name, args.dsin_name, ds_s3)

# Create Blob container
blob_service_client = blobtools.connect_blob(connect_str=args.blb_connect_str)
blobtools.create_or_update_container(blob_service_client, args.blob_container_name)

# Create an Azure blob dataset (output)
ds_lsb = LinkedServiceReference(reference_name=args.ls_blob_name)
dsOut_azure_blob = AzureBlobDataset(linked_service_name=ds_lsb, folder_path=args.blob_container_name)
dsOut = adf_client.datasets.create_or_update(args.rg_name, args.df_name, args.dsout_name, dsOut_azure_blob)

# Create a copy activity
asource = AmazonMWSSource()
bsink = BlobSink()
dsin_ref = DatasetReference(reference_name=args.dsin_name)
dsOut_ref = DatasetReference(reference_name=args.dsout_name)
copy_activity = CopyActivity(name=args.act_name, inputs=[dsin_ref], outputs=[dsOut_ref], source=asource, sink=bsink)

# Create a pipeline with the copy activity
params_for_pipeline = {}
p_obj = PipelineResource(activities=[copy_activity], parameters=params_for_pipeline)
p = adf_client.pipelines.create_or_update(args.rg_name, args.df_name, args.pipe_name, p_obj)

# Create a pipeline run
run_response = adf_client.pipelines.create_run(args.rg_name, args.df_name, args.pipe_name, parameters={})

