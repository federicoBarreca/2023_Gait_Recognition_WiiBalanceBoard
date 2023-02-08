import numpy as np
import pandas as pd
from scipy.spatial.distance import squareform, pdist


class Evaluation:

    def __init__(self):
        print("glich of us")

    @staticmethod
    def getId(encodedLabel, dataset, subject=True):
        id = dataset.labelToId(int(encodedLabel))
        if subject:
            return id[:-1]
        else:
            return id

    @staticmethod
    def computeDistanceMatrix(features, metric='euclidean'):
        return pd.DataFrame(squareform(pdist(np.array(features), metric=metric)))
        # columns=features.index, index=features.index)

    def verification(self, distanceMatrix, thresholds, features, dataset):
        # dictionary that will contain all the results
        results = {t: dict() for t in thresholds}
        rows, cols = distanceMatrix.shape
        for index, t in enumerate(thresholds):
            # For each treshold we test the method
            ga, fa, fr, gr = 0, 0, 0, 0
            for y in range(rows):
                rowLabel = self.getId(features.iloc[y].label, dataset)
                # results are grouped by label (here we're doing verification with multiple templates)
                groupedResults = dict()
                for x in range(cols):
                    # same probe => skip
                    if x == y: continue
                    # column label
                    colLabel = self.getId(features.iloc[x].label, dataset)
                    # storing results
                    groupedResults.setdefault(colLabel, []).append(distanceMatrix[y, x])
                for label in groupedResults:
                    # take minimum distance between templates
                    d = min(groupedResults[label])
                    if d < t:
                        # we have an acceptance, genuine or false?
                        if rowLabel == label:
                            ga += 1
                        else:
                            fa += 1
                    else:
                        # we have a rejection, genuine or false?
                        if rowLabel == label:
                            fr += 1
                        else:
                            gr += 1
            results[t] = {'gar': ga / rows, 'far': fa / (rows * (len(groupedResults) - 1)), 'frr': fr / rows,
                          'grr': gr / (rows * (len(groupedResults) - 1))}
            if index % (len(thresholds) // 10) == 0:
                print(
                    f"gar: {results[t]['gar']}\t far: {results[t]['far']}\t frr: {results[t]['frr']}\t grr: {results[t]['grr']}")
        return results

    @staticmethod
    def similarTo(probeIdx, features, distanceMatrix):
        similarities = list(
            sorted([i for i in range(distanceMatrix[probeIdx].shape[0])], key=lambda i: distanceMatrix[probeIdx][i]))
        similarities.remove(probeIdx)
        return similarities

    def identification(self, distanceMatrix, thresholds, features, dataset):
        # dictionary that will contain all the results
        results = {t: dict() for t in thresholds}
        rows, cols = distanceMatrix.shape
        di = {t: [0 for _ in range(rows)] for t in thresholds}
        _dir = {t: [0 for _ in range(rows)] for t in thresholds}
        for index, t in enumerate(thresholds):
            fa, gr = 0, 0
            for y in range(rows):
                rowLabel = self.getId(features.iloc[y].label, dataset)
                similarIndex = self.similarTo(y, features, distanceMatrix)
                if distanceMatrix[y][similarIndex[0]] <= t:
                    if rowLabel == self.getId(features.iloc[similarIndex[0]].label, dataset):
                        di[t][0] += 1
                        # find impostor case
                        for k in similarIndex:
                            if rowLabel != self.getId(features.iloc[k].label, dataset) and distanceMatrix[y][k] <= t:
                                fa += 1
                                break
                    else:
                        for k, indexAtRankK in enumerate(similarIndex):
                            if rowLabel == self.getId(features.iloc[indexAtRankK].label, dataset) and distanceMatrix[y][
                                indexAtRankK] <= t:
                                fa += 1
                                di[t][k] += 1
                                break
                else:
                    gr += 1
            _dir[t][0] = di[t][0] / rows
            for i in range(1, rows):
                _dir[t][i] = di[t][i] / rows + _dir[t][i - 1]
            results[t] = {'far': fa / rows, 'grr': gr / rows, 'dir': _dir[t], 'frr': 1 - _dir[t][0]}
            if index % (len(thresholds) // 10) == 0:
                print(
                    f"dir({t}, 1): {results[t]['dir'][0]}\t far: {results[t]['far']}\t frr: {results[t]['frr']}\t grr: {results[t]['grr']}")
        return results

    def cumulativeMatchingScore(self, distanceMatrix, features, dataset):
        rows, cols = distanceMatrix.shape
        cms = [0 for _ in range(rows)]
        for y in range(rows):
            rowLabel = self.getId(features.iloc[y].label, dataset)
            similarIndex = self.similarTo(y, features, distanceMatrix)
            for k, indexAtRankK in enumerate(similarIndex):
                if rowLabel == self.getId(features.iloc[indexAtRankK].label, dataset):
                    cms[k] += 1
                    break
        # rr
        cms[0] = cms[0] / rows
        for k in range(1, rows):
            cms[k] = cms[k] / rows + cms[k - 1]
        return cms

    def eval_verification(self, testDataset, features):
        dm = self.computeDistanceMatrix(features).to_numpy()
        thresholds = [t for t in range(0, 150, 1)]

        # verification
        print("Verification:")
        verificationResults = self.verification(dm, thresholds, features, testDataset)
        # plotVerificationResults(verificationResults)

    def eval_identification(self, testDataset, features):
        dm = self.computeDistanceMatrix(features).to_numpy()
        thresholds = [t for t in range(0, 150, 1)]

        # identification
        print("Identification:")
        identificationResults = self.identification(dm, thresholds, features, testDataset)
        cms = self.cumulativeMatchingScore(dm, features, testDataset)
        # plotIdentificationResults(identificationResults, cms)
