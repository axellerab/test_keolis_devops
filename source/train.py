import argparse
import os
import pandas as pd
import numpy as np
from sklearn.externals import joblib
from sklearn import neighbors

pd.set_option('display.max_columns', 500)

print("In train.py")
print("As a data scientist, this is where I use my training code.")

parser = argparse.ArgumentParser("train")

parser.add_argument("--input_data", type=str, help="input data")
parser.add_argument("--output", type=str, help="output_train directory")

args = parser.parse_args()

print("Argument 1: %s" % args.input_data)
print("Argument 2: %s" % args.output)

df = pd.read_csv(args.input_data, sep=';')
df["UT_time"] = df["UT_time"].str[:2].astype(int)

knn = neighbors.KNeighborsRegressor(n_neighbors=3)

x = np.array(df.iloc[:, 1:6])
y = np.array(df.loc[:, ["Short_wave_irradiation"]])
knn.fit(x, y)

# joblib.dump(knn, "/home/ava6210/Téléchargements/bestmodelever.pkl")
fname = args.output.split('/')[-1]
path = '/'.join(args.output.split('/')[:-1])


if not (args.output is None):
    os.makedirs(path+'/outputs', exist_ok=True)
    joblib.dump(knn, path+'/outputs/'+fname+ ".pkl")
    print("%s created" % args.output)

######### TEST A EFFACER ########################################
# path = '/home/ava6210/Téléchargements/meteodata.csv'
# df = pd.read_csv(path, sep=';')
# df["UT_time"] = df["UT_time"].str[:2].astype(int)
# from sklearn import neighbors
#
# knn = neighbors.KNeighborsRegressor(n_neighbors=3)
#
# x = np.array(df.iloc[:, 1:6])
# y = np.array(df.loc[:, ["Short_wave_irradiation"]])
#
# y_ = knn.fit(x, y).predict(x)
#
# joblib.dump(knn, "/home/ava6210/Téléchargements/bestmodelever.pkl")
