#!/usr/bin/python

import sys, getopt
import data_preprocessing as processor
import pickle

trained_Models = {
    'ALL' : {
        "__transformerFilename" : "",
        "__classifierFilename" : "" 
        },
    'MUC' : {
        "__transformerFilename" : "",
        "__classifierFilename" : "" 
        },
    'STR_ALL' : {
        "__transformerFilename" : "",
        "__classifierFilename" : "" 
        },
    'STR_IN' : {
        "__transformerFilename" : "",
        "__classifierFilename" : "" 
        },
    'STR_SN' : {
        "__transformerFilename" : "",
        "__classifierFilename" : "" 
        }          
    }

def main(argv):
    inputfile = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print('subchallenge1.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('subchallenge1.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
    
    processingData = processor.MMChallengeData(inputfile);
    x, y, modelType = processingData.preprocessPrediction();
    x, y = processingData.df_reduce(x,y, scaler="scaler", fit = False, filename = trained_Models[modelType]["__transformerFilename"])
    
    processingData.dataDict = {"genomic" : (x,[],y) }
    processingData.__generateDataTypePresence()
    
    clf = pickle.load(trained_Models[modelType]["__classifierFilename"])
    
    
    mod = processor.MMChallengePredictor(
        mmcdata = processingData,
        predict_fun = lambda x: clf.predict(x)[0],
        confidence_fun = lambda x: 1 - min(clf.predict_proba(x)[0]),
        data_types = ["genomic"],
        single_vector_apply_fun = lambda x: x,
        multiple_vector_apply_fun = lambda x: x.values.reshape(1,-1)
    )
    
    outputDF = mod.predict_dataset()
    outputDF.to_csv(outputfile)

if __name__ == "__main__":
    main(sys.argv[1:])