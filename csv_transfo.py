import os

def detect_full_path(path, pattern):
    try:
        file_name = [e for e in os.listdir(path) if pattern in e][0]
        if len([e for e in os.listdir(path) if pattern in e]) > 1:
            print('plusieurs fichiers matchent')
    except IndexError:
        print('fichier non reconnu')
    return path + '/' + file_name


def lecture(path):
    with open(path, 'r') as fichier:
        lignes = fichier.read()
    return lignes

def transform_merra_file(path, merra_str):
    with open(path, 'w') as csvfile:
        to_write = str(merra_str.split('# ')[-1])
        to_write_list = to_write.split('\n')
        to_write_list[0] = to_write_list[0].replace(' ', '_').replace('-', '_')
        csvfile.write('\n'.join(to_write_list))
    return path
