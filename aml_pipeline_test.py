
# from azureml.data.azure_storage_datastore import AzureBlobDatastore
# import blobtools
# import joblib
from azureml.core import Workspace
from azureml.core import Run
from azureml.core.runconfig import RunConfiguration
from azureml.core.model import Model
import argparse

# VARIABLES #################
parser = argparse.ArgumentParser()
parser.add_argument("--sub", help="SubscriptionID.", type=str)
parser.add_argument("--cliid", help="ClientID ou AppID.", type=str)
parser.add_argument("--pwd", help="Password.", type=str)
parser.add_argument("--tntid", help="TenantID.", type=str)
parser.add_argument("--basename", help="Prefix for all names.", type=str)
parser.add_argument("--loc", help="Location.", type=str)
parser.add_argument("--datafilepath", help="data file input name.", type=str)
args = parser.parse_args()

sub_id = args.sub
res_grp = args.basename + "-RG"
workspace_n = args.basename + "-AML-WS"
data_ref = args.datafilepath.split("/")[-1][:-4]
data_filepath = args.datafilepath
model_basename = "model-test"
model_pklname = "modknn"

# Configurer des ressources Machine Learning
# help(Workspace)
ws = Workspace(subscription_id=sub_id, resource_group=res_grp, workspace_name=workspace_n)

# Configurer un magasin de données
# Default datastore
def_data_store = ws.get_default_datastore()

# Configurer la référence de données
# créer une source de données susceptible d’être référencée dans un pipeline en tant qu’entrée ou étape.
# Dans un pipeline, une source de données est représentée par un objet DataReference.
from azureml.data.data_reference import DataReference
blob_input_data = DataReference(
    datastore=def_data_store,
    data_reference_name=data_ref,
    path_on_datastore=data_filepath)

# Les données intermédiaires (ou la sortie d’une étape) sont représentées par un objet PipelineData.
from azureml.pipeline.core import PipelineData
output_data1 = PipelineData(
    "output_data1",
    datastore=def_data_store,
    output_name=model_pklname)

# Configurer la cible de calcul
# créer une capacité de calcul Azure Machine Learning pour exécuter vos étapes
from azureml.core.compute import ComputeTarget, AmlCompute
compute_name = "computeuh"
vm_size = 'STANDARD_D2_V2'
if compute_name in ws.compute_targets:
    compute_target = ws.compute_targets[compute_name]
    if compute_target and type(compute_target) is AmlCompute:
        print('Found compute target: ' + compute_name)
else:
    print('Creating a new compute target...')
    provisioning_config = AmlCompute.provisioning_configuration(vm_size=vm_size,
                                                                min_nodes=0,
                                                                max_nodes=2)
    # create the compute target
    compute_target = ComputeTarget.create(
        ws, compute_name, provisioning_config)

    # Can poll for a minimum number of nodes and for a specific timeout.
    # If no min node count is provided it will use the scale settings for the cluster
    compute_target.wait_for_completion(show_output=True, min_node_count=None, timeout_in_minutes=40)

    # For a more detailed view of current cluster status, use the 'status' property
    print(compute_target.status.serialize())

project_folder = 'source'

# Composer les étapes de votre pipeline
from azureml.core.environment import CondaDependencies
# myenv = Environment(name="myenv")
conda_dep = CondaDependencies()
conda_dep.add_conda_package("scikit-learn")
conda_dep.add_conda_package("joblib")
conda_dep.add_conda_package("numpy")
conda_dep.add_conda_package("pandas")


conf = RunConfiguration(script="train.py", conda_dependencies=conda_dep)
from azureml.pipeline.steps import PythonScriptStep
trainStep = PythonScriptStep(
    script_name="train.py",
    arguments=["--input_data", blob_input_data, "--output", output_data1],
    inputs=[blob_input_data],
    outputs=[output_data1],
    compute_target=compute_target,
    source_directory=project_folder,
    runconfig=conf,
    allow_reuse=False
)

# list of steps to run
compareModels = [trainStep]

from azureml.pipeline.core import Pipeline

# Build the pipeline
pipeline1 = Pipeline(workspace=ws, steps=[compareModels])
run = Run.get_context()

# Envoyer le pipeline
from azureml.core import Experiment

# Submit the pipeline to be run
pipeline_run1 = Experiment(ws, 'Compare_Models_Exp').submit(pipeline1)
pipeline_run1.wait_for_completion(False, 0, True)


#Récupération du run id de la step 1 sur 1 de la pipeline
step1_runid = [e for e in pipeline_run1.get_steps()][0].id
#création du path complet dans le blob storage
path_model_datastore = "azureml/"+step1_runid+"/outputs/"
#download en local du modele
def_data_store.download(target_path='datastore', prefix=path_model_datastore)
#chargement dans la workspace a partir du modele download en local
model = Model.register(workspace=ws, model_path='datastore/'+path_model_datastore+model_pklname+'.pkl', model_name=model_basename)


#Create environment file
from azureml.core.conda_dependencies import CondaDependencies

myenv = CondaDependencies()
myenv.add_conda_package("scikit-learn")
myenv.add_pip_package("azureml-defaults")
myenv.add_conda_package("numpy")
myenv.add_conda_package("pandas")

# import os
# old_wd = os.getcwd()
# os.chdir(old_wd+"/source")

with open("myenv.yml", "w") as f:
    f.write(myenv.serialize_to_string())

#Review the content of the myenv.yml file:
with open("myenv.yml", "r") as f:
    print(f.read())

# register image
print("register image")
from azureml.core.image import Image, ContainerImage

image_config = ContainerImage.image_configuration(runtime= "python",
                                execution_script="score.py",
                                conda_file="myenv.yml",
                                tags = {"data": "meteosalut","method": "knn"},
                                description = "Image test knn sur donnees meteo")

# os.chdir(old_wd)

image = Image.create(name = "myimage1",
                    # this is the model object. note you can pass in 0-n models via this list-type parameter
                    # in case you need to reference multiple models, or none at all, in your scoring script.
                    models = [model],
                    image_config = image_config,
                    workspace = ws)
image.wait_for_creation(True)

#Create a container configuration file
from azureml.core.webservice import AciWebservice

aciconfig = AciWebservice.deploy_configuration(cpu_cores=1, memory_gb=1,tags={"data": "meteo","method": "knn"},description='test knn sur donnees meteo')

# Deploy
print("Deploy")
from azureml.core.webservice import Webservice
from azureml.core.model import InferenceConfig
from azureml.core.environment import Environment

myenv = Environment.from_conda_specification(name="myenv", file_path="myenv.yml")
inference_config = InferenceConfig(entry_script="score.py", environment=myenv)

# service = Model.deploy(workspace=ws,
#                        name='sklearn-knn-meteotest',
#                        models=[model],
#                        inference_config=inference_config,
#                        deployment_config=aciconfig)
#
# service.wait_for_deployment(show_output=True)


aci_service_name = 'aci-service-meteotest'
service = Webservice.deploy_from_image(deployment_config = aciconfig,
                                           image = image,
                                           name = aci_service_name,
                                           workspace = ws)
service.wait_for_deployment(True)



