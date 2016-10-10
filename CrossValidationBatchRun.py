# This code runs cross validation to the models developed, not intended for
# others' use.
# It uses the example data as the example.

# argument parsing
import argparse
argparser = argparse.ArgumentParser(description='Run cross validation.')
argparser.add_argument('algo', help='Algorithm to run. Options: '+', '.join(list(allowed_algos)))
argparser.add_argument('word2vec_path', help='Path of the binary Word2Vec model.')
args = argparser.parse_args()

# import other libraries
from gensim.models import Word2Vec
import numpy as np

from classifiers import allowed_algos
import classifiers.SumWord2VecClassification as sumwv
import classifiers.AutoencoderEmbedVecClassification as auto
import classifiers.CNNEmbedVecClassification as cnn
import data.data_retrieval as ret
from utils import AlgorithmNotExistException

# loading Word2Vec model
print "Loading embedding model..."
wvmodel = Word2Vec.load_word2vec_format(args.word2vec_path, binary=True)

# data partition
partnum = 5
repetitions = 6
length = 15
master_classdict = ret.retrieve_data_as_dict('data/shorttext_exampledata.csv')
partitioned_classdicts = []
for grp in range(repetitions):
    shuffled = {}
    for classlabel in master_classdict:
        shuffled[classlabel] = list(master_classdict[classlabel])
        np.random.shuffle(shuffled[classlabel])
    for part in range(partnum):
        testdict = {}
        traindict = {}
        for classlabel in shuffled:
            testdict[classlabel] = shuffled[classlabel][part*length:(part+1)*length]
            traindict[classlabel] = np.append(shuffled[classlabel][:part*length], shuffled[classlabel][(part+1)*length:])
        partitioned_classdicts.append({'train': traindict,
                                       'test': testdict})

print 'Number of tests = ', len(shuffled)

accuracies = []

for classdicts in partitioned_classdicts:
    # train model
    if args.algo=='sumword2vec':
        classifier = sumwv.SumEmbeddedVecClassifier(wvmodel, classdicts['train'])
    elif args.algo=='autoencoder':
        classifier = auto.AutoEncoderWord2VecClassifier(wvmodel, classdicts['train'])
    elif args.algo=='cnn':
        classifier = cnn.CNNEmbeddedVecClassifier(wvmodel, classdicts['train'], 2)
    else:
        raise AlgorithmNotExistException(args.algo)
    classifier.train()

    numdata = 0
    numcorrects = 0
    for classlabel in classdicts['test']:
        for shorttext in classdicts['test'][classlabel]:
            predictions = classifier.score(shorttext)
            predicted_label = max(predictions.items(), key=lambda s: s[1])[0]
            numdata += 1
            numcorrects += 1 if predicted_label==classlabel else 0

    accuracies.append(float(numcorrects)/numdata)