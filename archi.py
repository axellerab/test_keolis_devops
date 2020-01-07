import argparse
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
from azureml.core import Workspace
import time

parser = argparse.ArgumentParser()
parser.add_argument("--sub", help="SubscriptionID.", type=str)
parser.add_argument("--cliid", help="ClientID ou AppID.", type=str)
parser.add_argument("--pwd", help="Password.", type=str)
parser.add_argument("--tntid", help="TenantID.", type=str)
parser.add_argument("--basename", help="Prefix for all names.", type=str)
parser.add_argument("--loc", help="Location.", type=str)
args = parser.parse_args()

print('SubscriptionID :' + args.sub)

# Create credentials
credentials = ServicePrincipalCredentials(client_id=args.cliid,
                                          secret=args.pwd,
                                          tenant=args.tntid)
resource_client = ResourceManagementClient(credentials, args.sub)
adf_client = DataFactoryManagementClient(credentials, args.sub)

# Create resources group
#resource_client.resource_groups.create_or_update(args.basename + '-RG', {'location': args.loc})

# Create a data factory
df_resource = Factory(location=args.loc)
df = adf_client.factories.create_or_update(args.basename + '-RG', args.basename + '-DF', df_resource)
while df.provisioning_state != 'Succeeded':
    df = adf_client.factories.get(args.basename + '-RG', args.basename + '-DF')
    time.sleep(1)

# Create a machine learning workspace
#ws = Workspace.create(
#            name=args.basename + '-WS',
#            subscription_id=args.sub,
#            resource_group=args.basename + '-RG',
#            create_resource_group=False,
#            location=args.loc)

