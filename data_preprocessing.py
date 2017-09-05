import os.path as path
import pandas as pd

GCT_NAME = "globalClinTraining.csv"
SAMP_ID_NAME = "SamplId"
DATA_PROPS = {
    "MA": {
        "__folder": "Microarray Data",
        "probe": "MA_probeLevelExpFile",
        "gene": "MA_geneLevelExpFile"
    },
    "RNASeq": {
        "__folder": "RNA-Seq Data",
        "trans": "RNASeq_transLevelExpFile",
        "gene": "RNASeq_geneLevelExpFile"
    }
}


def log_preprocessing(df):
    pass


class MMChallengeData(object):
    def __init__(self, parentFolder):
        self.__parentFolder = parentFolder
        self.clinicalData = pd.read_csv(path.join(self.__parentFolder, "Clinical Data", GCT_NAME))
        self.clinicalData["Patient Index"] = self.clinicalData.index
        self.clinicalData.index = self.clinicalData["Patient"]

    def getData(self, datype, level, clinicalVariables=["D_Age", "D_ISS"], outputVariable="HR_FLAG", sep=","):
        type_level = DATA_PROPS[datype][level]
        type_level_sid = type_level + SAMP_ID_NAME
        baseCols = ["Patient", type_level, type_level_sid]
        subcd = self.clinicalData[baseCols + clinicalVariables + [outputVariable]].dropna(subset=baseCols)
        dfiles = subcd[type_level].dropna().unique()
        print(dfiles)
        dframes = [pd.read_csv(path.join(self.__parentFolder, "Expression Data", DATA_PROPS[datype]["__folder"], dfile),
                               index_col=[0], sep = sep).T for dfile in dfiles]

        if len(dframes) > 1:
            df = pd.concat(dframes)
        else:
            df = dframes[0]

        df = df.loc[subcd[type_level_sid], :]
        df.index = subcd["Patient"]
        return df, subcd[clinicalVariables], subcd[outputVariable]


if __name__ == '__main__':

    mmcd = MMChallengeData("/home/skapur/synapse/syn7222203")
    mmcd.clinicalData["RNASeq_geneLevelExpFile"]
    # mmcd = MMChallengeData("C:\\Users\\vitor\\synapse\\syn7222203")
    # MA_gene = mmcd.getData("MA","gene")
    RNA_gene, RNA_gene_cd, RNA_gene_output = mmcd.getData("RNASeq", "gene", sep=",")
    RNA_trans, RNA_trans_cd, RNA_trans_output = mmcd.getData("RNASeq", "trans", sep="\t")


    import numpy as np
    from sklearn.naive_bayes import GaussianNB
    from sklearn.preprocessing import StandardScaler
    from sklearn.feature_selection import SelectPercentile
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import cross_validate, GridSearchCV
    from sklearn.metrics import accuracy_score, recall_score, f1_score, log_loss
    from sklearn_pandas import DataFrameMapper


    def report(cvr):
        for name, array in cvr.items():
            print(name+" : "+str(np.mean(array))+" +/- "+str(np.std(array)))


    def prepare_data(X_gene, X_trans, y_orig, dropnaAxis=1):
        X = pd.concat([X_gene, X_trans], axis=1).dropna(axis=dropnaAxis)
        y = y_orig[X.index]
        valid_samples = y != "CENSORED"
        X, y = X[valid_samples], y[valid_samples] == "TRUE"
        return X, y

    MA_gene, MA_gene_cd, MA_gene_output = mmcd.getData("MA", "gene", sep=",")
    MA_probe, MA_probe_cd, MA_probe_output = mmcd.getData("MA", "probe", sep=",")

    Xr, yr = prepare_data(MA_gene, MA_probe, MA_gene_output, 1)
    Xm, ym = prepare_data(RNA_gene, RNA_trans, RNA_gene_output, 0)

    Xm = StandardScaler().fit_transform(Xm, ym)
    Xr = StandardScaler().fit_transform(Xr, yr)

    X = pd.concat([Xr,Xm], axis=0).dropna(axis=1)
    y = pd.concat([yr,ym])[X.index]

    pipeline_factory = lambda clf: Pipeline(steps=[("scale", StandardScaler()), ("feature_selection",SelectPercentile(percentile=30)), ("classify", clf)])

    cv = cross_validate(pipeline_factory(GaussianNB()), X, y, scoring=["accuracy","recall","f1","neg_log_loss","precision"], cv = 10)
    report(cv)
