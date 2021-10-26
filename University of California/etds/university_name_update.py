import os
import json


def main():
    university = 'ucd' #TODO: Change university name here
    etddirs = os.listdir(university)
    for etddir in etddirs:
        textFilePath = os.path.join(university,etddir,etddir+'.txt')
        # Read file
        filee = open(textFilePath, 'r')
        content = filee.readline()
        metadata = json.loads(content)
        
        # Upate with university key if not exist
        if 'university' not in metadata.keys():
            metadata['university'] = university # add(university:university)
        
        # Write json to the file
        with open(textFilePath, 'w') as json_file:
            json.dump(metadata, json_file)
        

if __name__ == '__main__':
    main()