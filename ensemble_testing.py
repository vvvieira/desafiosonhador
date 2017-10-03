
import numpy as np
import pandas as pd
import pickle
import sys

from sklearn.feature_selection import SelectPercentile
from sklearn.preprocessing import MaxAbsScaler, QuantileTransformer, MinMaxScaler, StandardScaler

#Models
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier, BaggingClassifier, AdaBoostClassifier, VotingClassifier

from data_preprocessing import MMChallengeData, MMChallengePredictor
from genomic_data_test import df_reduce, cross_val_function

def report (cv_res):
    print("="*40)
    for name, array in cv_res.items():
        print(str(name) + ": %0.4f (+/- %0.4f)" % (np.mean(array), np.std(array)))
    print("="*40)

#Load data
data_folder = '.\Expression Data\All Data'
clin_file = '.\Clinical Data\sc2_Training_ClinAnnotations.csv'
mmcd = MMChallengeData(clin_file)
mmcd.generateDataDict(clinicalVariables=["D_Age", "D_ISS"], outputVariable="HR_FLAG", directoryFolder=data_folder, columnNames=None, NARemove=[True, False])

#Transformers
scl = MaxAbsScaler()
fts = SelectPercentile(percentile = 30)

# =========================
#          RNA-SEQ
# =========================

#Prepare data
Xrseq, cdrseq, yrseq = mmcd.dataDict[("RNASeq","gene")]
Xnrseq = Xrseq.dropna(axis = 1)
yrseq = yrseq == "TRUE"
yrseq = yrseq.astype(int)

X_rseq_t, y_rseq_t, fts_vector = df_reduce(Xnrseq, yrseq, scl, fts, True, filename = 'transformers_rna_seq.sav')

# =============================
#          MICROARRAYS
# =============================

Xma, cdma, yma = mmcd.dataDict[("MA","gene")]
Xnma = Xma.dropna(axis = 1)
yma = yma == "TRUE"
yma = yma.astype(int)

X_ma_t, y_ma_t, fts_vector = df_reduce(Xnma, yma, scl, fts, True, filename = 'transformers_microarrays.sav')


# =============================
#          ENSEMBLE
# =============================

clf1 = LogisticRegression(random_state = 1, solver = 'newton-cg', C = 1, penalty = "l2", tol = 0.001, multi_class = 'multinomial')
clf2 = RandomForestClassifier(random_state = 1, max_depth = 5, criterion = "entropy", n_estimators = 100)
clf3 = GaussianNB()
clf4 = SVC(kernel = "linear", C = 1, probability = True, gamma = 0.0001)
clf5 = MLPClassifier(solver = 'adam', activation = "relu", hidden_layer_sizes = (50,25), alpha = 0.001)
eclf1 = VotingClassifier(estimators=[('lr', clf1), ('rf', clf2), ('gnb', clf3), ('svm', clf4), ('nnet', clf5)],
                         voting = 'soft', n_jobs = -1, weights = [2,1,1,5,5])
#eclf1 = eclf1.fit(X_rseq_t, y_rseq_t)

#RNA-Seq
cv = cross_val_function(X_rseq_t, y_rseq_t, clf = eclf1)

#Microarrays
cv = cross_val_function(X_ma_t, y_ma_t, clf = eclf1)
report(cv)


clf = MLPClassifier(solver = 'adam', activation = "relu", hidden_layer_sizes = (50,25), alpha = 0.001)
cv = cross_val_function(X_rseq_t, y_rseq_t, clf = clf)
report(cv)


# =========================
#          PLOTS
# =========================

# import matplotlib as plt
# plt.use('Qt5Agg')
# import matplotlib.pyplot as plt
# #import PyQt5
# #import matplotlib.pyplot as plt
#
# clf1 = LogisticRegression(random_state = 1, solver = 'newton-cg', C = 1, penalty = "l2", tol = 0.001, multi_class = 'multinomial')
# clf2 = RandomForestClassifier(random_state = 1, max_depth = 5, criterion = "entropy", n_estimators = 100)
# clf3 = GaussianNB()
# eclf = VotingClassifier(estimators=[('lr', clf1), ('rf', clf2), ('gnb', clf3)], voting = 'soft', n_jobs = -1, weights = [1, 1, 5])
#
# # predict class probabilities for all classifiers
# probas = [c.fit(X_rseq_t, y_rseq_t).predict_proba(X_rseq_t) for c in (clf1, clf2, clf3, eclf)]
#
# # get class probabilities for the first sample in the dataset
# class1_1 = [pr[0, 0] for pr in probas]
# class2_1 = [pr[0, 1] for pr in probas]
#
# # plotting
# N = 4  # number of groups
# ind = np.arange(N)  # group positions
# width = 0.35  # bar width
#
# fig, ax = plt.subplots()
#
# # bars for classifier 1-3
# p1 = ax.bar(ind, np.hstack(([class1_1[:-1], [0]])), width, color='green', edgecolor='k')
# p2 = ax.bar(ind + width, np.hstack(([class2_1[:-1], [0]])), width, color='lightgreen', edgecolor='k')
#
# # bars for VotingClassifier
# p3 = ax.bar(ind, [0, 0, 0, class1_1[-1]], width, color='blue', edgecolor='k')
# p4 = ax.bar(ind + width, [0, 0, 0, class2_1[-1]], width, color='steelblue', edgecolor='k')
#
# # plot annotations
# plt.axvline(2.8, color='k', linestyle='dashed')
# ax.set_xticks(ind + width)
# ax.set_xticklabels(['LogisticRegression\nweight 1',
#                     'GaussianNB\nweight 1',
#                     'RandomForestClassifier\nweight 5',
#                     'VotingClassifier\n(average probabilities)'],
#                    rotation=40,
#                    ha='right')
# plt.ylim([0, 1])
# plt.title('Class probabilities for sample 1 by different classifiers')
# plt.legend([p1[0], p2[0]], ['class 1', 'class 2'], loc='upper left')
# plt.show()













