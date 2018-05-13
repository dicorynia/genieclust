import numpy as np
from genieclust.hdbscan import *
from genieclust.inequity import*
from genieclust.mst import *
import time
import gc

def mutual_reachability_distance_old(D, M):
    if M <= 2: return D.copy()
    argD = np.argsort(D, axis=1)
    # argD should be read row-wise, i.e.,
    # argD[i,:] is the ordering permutation for ith point's NNs
    Dcore = D[np.arange(D.shape[0]),argD[:, M-1]]
    res = np.maximum(np.maximum(D, Dcore.reshape(-1, 1)), Dcore.reshape(1, -1))
    res[np.arange(D.shape[0]),np.arange(D.shape[0])] = 0.0
    return res




import scipy.spatial.distance
import numpy as np
path = "benchmark_data"

def test_hdbscan():
    for dataset in ["s1", "Aggregation", "WUT_Smile", "unbalance", "pathbased", "a1"]:
        X = np.loadtxt("%s/%s.data.gz" % (path,dataset), ndmin=2)
        labels = np.loadtxt("%s/%s.labels0.gz" % (path,dataset), dtype='int')
        label_counts = np.unique(labels,return_counts=True)[1]
        k = len(label_counts)
        D = scipy.spatial.distance.pdist(X)
        D = scipy.spatial.distance.squareform(D)

        for M in [2, 3, 5, 10]:
            gc.collect()
            t0 = time.time()
            D1 = mutual_reachability_distance(D, M)
            print("%-20s\tM=%2d\tt=%.3f" % (dataset, M, time.time()-t0), end="\t")
            t0 = time.time()
            D2 = mutual_reachability_distance_old(D, M)
            print("t_old=%.3f" % (time.time()-t0,))
            dist = np.mean((D1 - D2)**2)
            assert dist < 1e-12

            for k in [2, 3, 5]:
                mst = MST_pair(D1)
                cl = HDBSCAN(k).fit_predict_from_mst(mst)+1
                assert max(cl) == k
                print(np.unique(cl, return_counts=True))

            D1 = None
            D2 = None

if __name__ == "__main__":
    test_hdbscan()
