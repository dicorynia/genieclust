"""The Genie+ Clustering Algorithm

Copyright (C) 2018-2020 Marek Gagolewski (https://www.gagolewski.com)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
may be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import numpy as np
from . import internal
import scipy.spatial.distance
from sklearn.base import BaseEstimator, ClusterMixin
import sklearn.neighbors
import warnings
import math

# TODO: delme
import time

# TODO: ???
try:
    import faiss
except ImportError:
    pass



class Genie(BaseEstimator, ClusterMixin):
    """The Genie+ Clustering Algorithm with optional smoothing and
    noise point detection (for M>1)

    Based on: Gagolewski M., Bartoszuk M., Cena A.,
    Genie: A new, fast, and outlier-resistant hierarchical clustering algorithm,
    Information Sciences 363, 2016, pp. 8-23. doi:10.1016/j.ins.2016.05.003

    A new hierarchical clustering linkage criterion: the Genie algorithm
    links two clusters in such a way that an inequity measure
    (namely, the Gini index) of the cluster sizes doesn't go far beyond
    some threshold. The introduced method most often outperforms
    the Ward or average linkage, k-means, spectral clustering,
    DBSCAN, Birch, and many others in terms of the clustering
    quality while - at the same time - it retains the speed of
    the single linkage algorithm.

    This is a new implementation of the Genie algorithm that requires
    O(n_samples*sqrt(n_samples))-time given a minimum spanning tree
    of the pairwise distance graph.
    The clustering can also be computed with respect to the
    mutual reachability distance (based, e.g., on the Euclidean metric),
    which is used in the definition of the HDBSCAN* algorithm, see
    R. Campello, D. Moulavi, A. Zimek, J. Sander, Hierarchical density
    estimates for data clustering, visualization, and outlier detection,
    ACM Transactions on Knowledge Discovery from Data 10(1):5:1–5:51, 2015.
    doi:10.1145/2733381.

    The Genie correction together with the smoothing factor M>2 (note that
    M==2 corresponds to the original distance) gives a robustified version of
    the HDBSCAN algorithm that is able to yield a predefined number of clusters,
    and hence  not dependent on the original DBSCAN's somehow magical
    `eps` parameter or the HDBSCAN Python package's `min_cluster_size` one.

    Note that the resulting partition tree (dendrogram) might violate
    the ultrametricity property (merges might occur at nonmonotone levels).
    Hence, distance threshold-based stopping criterion is not implemented.




    Parameters
    ----------

    n_clusters : int >= 0, default=2
        Number of clusters to detect. Note that depending on the dataset
        and approximations used (see parameter `exact`), the actual
        partition size can be smaller.
        n_clusters==1 can act as a noise point/outlier detector (if M>1).
        n_clusters==0 computes the whole dendrogram but doesn't generate
        any particular cuts.
    gini_threshold : float in [0,1], default=0.3
        The threshold for the Genie correction, i.e.,
        the Gini index of the cluster size distribution.
        Threshold of 1.0 disables the correction.
        Low thresholds highly penalise the formation of small clusters.
    M : int, default=1
        Smoothing factor. M=1 gives the original Genie algorithm.
    affinity : str, default="euclidean"
        Metric used to compute the linkage. One of: "euclidean" (synonym: "l2"),
        "manhattan" (a.k.a. "l1" and "cityblock"), "cosine" or "precomputed".
        If "precomputed", a complete pairwise distance matrix
        is needed as input (argument X) for the fit() method.
    compute_full_tree : bool, default=True
        If True, only a partial hierarchy is determined so that
        at most n_clusters are generated. Saves some time if you think you know
        how many clusters to expect, but do you?
    postprocess : str, one of "boundary" (default), "none", "all"
        In effect only if M>1. By default, only "boundary" points are merged
        with their nearest "core" points. To force a classical
        n_clusters-partition of a data set (with no notion of noise),
        choose "all".
    exact : bool, default=True
        TODO: NOT IMPLEMENTED YET
        ........................................................................
        If False, the minimum spanning tree is approximated
        based on the nearest neighbours graph. Finding nearest neighbours
        in low dimensional spaces is usually fast. Otherwise,
        the algorithm will need to inspect all pairwise distances,
        which gives the time complexity of O(n_samples*n_samples*n_features).
    cast_float32 : bool, default=True
        Allow casting input data to a float32 dense matrix
        (for efficiency reasons == decreases the run-time ~2x times
        at a cost of greater memory usage).
        TODO: Note that some nearest neighbour search
        methods require float32 data anyway.
        TODO: Might be a problem if the input matrix is sparse, but
        with don't support this yet.



    Attributes
    ----------

    labels_ : ndarray, shape (n_samples,) or None
        Detected cluster labels of each point:
        an integer vector c with c[i] denoting the cluster id
        (in {0, ..., n_clusters-1}) of the i-th object.
        If M>1, noise points are labelled -1.
    n_clusters_ : int
        The number of clusters detected by the algorithm.
        If 0, then labels_ are not set.
        Note that the actual number might be larger than the n_clusters
        requested, for instance, if there are many noise points.
    n_samples_ : int
        The number of points in the fitted dataset.
    n_features_ : int or None
        The number of features in the fitted dataset.
    children_ : ndarray, shape (n_samples-1, 2)
        The i-th row provides the information on the clusters merged at
        the i-th iteration. Noise points are merged first, with
        the corresponding distances_[i] of 0.
        See the description of Z[i,0] and Z[i,1] in
        scipy.cluster.hierarchy.linkage. Together with distances_ and
        counts_, this forms the linkage matrix that can be used for
        plotting the dendrogram.
        Only available if `compute_full_tree` is True.
    distances_ : ndarray, shape (n_samples-1,)
        Distance between the two clusters merged at the i-th iteration.
        Note Genie does not guarantee that that distances are
        ordered increasingly (do not panic, there are some other hierarchical
        clustering linkages that also violate the ultrametricity property).
        See the description of Z[i,2] in scipy.cluster.hierarchy.linkage.
        Only available if `compute_full_tree` is True.
    counts_ : ndarray, shape (n_samples-1,)
        Number of elements in a cluster created at the i-th iteration.
        See the description of Z[i,3] in scipy.cluster.hierarchy.linkage.
        Only available if `compute_full_tree` is True.
    """

    def __init__(self,
            n_clusters=2,
            gini_threshold=0.3,
            M=1,
            affinity="euclidean",
            compute_full_tree=True,
            postprocess="boundary",
            exact=True,
            cast_float32=True
        ):
        self.n_clusters = n_clusters
        self.gini_threshold = gini_threshold
        self.M = M
        self.affinity = affinity
        self.compute_full_tree = compute_full_tree
        self.postprocess = postprocess
        self.exact = exact
        self.cast_float32 = cast_float32

        self.n_clusters_  = 0 # should not be confused with self.n_clusters
        self.n_samples_   = 0
        self.n_features_  = 0
        self.labels_      = None
        self.children_    = None
        self.distances_   = None
        self.counts_      = None
        self._links_      = None
        self._iters_      = None
        self._mst_dist_   = None
        self._mst_ind_    = None
        self._nn_dist_    = None
        self._nn_ind_     = None
        self._d_core_     = None


    def fit(self, X, y=None):
        """Perform clustering of the X dataset.
        See the labels_ and n_clusters_ attributes for the clustering result.


        Parameters
        ----------

        X : ndarray, shape (n_samples, n_features) or (n_samples, n_samples)
            A matrix defining n_samples in a vector space with n_features.
            Hint: it might be a good idea to normalise the coordinates of the
            input data points by calling
            X = ((X-X.mean(axis=0))/X.std(axis=None, ddof=1)).astype(np.float32, order="C", copy=False) so that the dataset is centered at 0 and
            has total variance of 1. This way the method becomes
            translation and scale invariant.
            However, if affinity="precomputed", then X is assumed to define
            all pairwise distances between n_samples.
        y : None
            Ignored.


        Returns
        -------

        self
        """
        cur_state = dict()

        _affinity_options = ("euclidean", "l2", "manhattan", "l1",
                             "cityblock", "cosine", "precomputed")
        cur_state["affinity"] = str(self.affinity).lower()
        if cur_state["affinity"] not in _affinity_options:
            raise ValueError("postprocess should be one of %r"%_affinity_options)

        n_samples  = X.shape[0]
        if cur_state["affinity"] == "precomputed":
            n_features = None
            if X.shape[0] != X.shape[1]:
                raise ValueError("X must be a square matrix that gives all the pairwise distances")
        else:
            n_features = X.shape[1]


        cur_state["n_clusters"] = int(self.n_clusters)
        if cur_state["n_clusters"] < 0:
            raise ValueError("n_clusters must be >= 0")

        cur_state["gini_threshold"] = float(self.gini_threshold)
        if not (0.0 <= cur_state["gini_threshold"] <= 1.0):
            raise ValueError("gini_threshold not in [0,1]")

        cur_state["M"] = int(self.M)
        if not 1 <= cur_state["M"] <= n_samples:
            raise ValueError("M must be in [1, n_samples]")

        _postprocess_options = ("boundary", "none", "all")
        cur_state["postprocess"] = str(self.postprocess).lower()
        if cur_state["postprocess"] not in _postprocess_options:
            raise ValueError("postprocess should be one of %r"%_postprocess_options)

        cur_state["exact"] = bool(self.exact)
        cur_state["cast_float32"] = bool(self.cast_float32)
        cur_state["compute_full_tree"] = bool(self.compute_full_tree)

        mst_dist = None
        mst_ind  = None
        nn_dist  = None
        nn_ind   = None
        d_core   = None

        if cur_state["cast_float32"]:
            # faiss supports float32 only
            # warning if sparse!!
            X = X.astype(np.float32, order="C", copy=False)

        if not cur_state["exact"]:
            if cur_state["affinity"] == "precomputed":
                raise ValueError('exact=True with affinity="precomputed"')

            #raise NotImplementedError("approximate method not implemented yet")

            assert cur_state["affinity"] in ("euclidean", "l2")

            actual_n_neighbors = min(32, int(math.ceil(math.sqrt(n_samples))))
            actual_n_neighbors = max(actual_n_neighbors, cur_state["M"]-1)
            actual_n_neighbors = min(n_samples-1, actual_n_neighbors)

            # t0 = time.time()
            #nn = sklearn.neighbors.NearestNeighbors(n_neighbors=actual_n_neighbors, **cur_state["nn_params"])
            #nn_dist, nn_ind = nn.fit(X).kneighbors()
            # print("T=%.3f" % (time.time()-t0), end="\t")

            # FAISS - `euclidean` and `cosine` only!



            # TODO:  cur_state["metric"], cur_state["metric_params"]
            #t0 = time.time()
            # the slow part:
            nn = faiss.IndexFlatL2(n_features)
            nn.add(X)
            nn_dist, nn_ind = nn.search(X, actual_n_neighbors+1)
            #print("T=%.3f" % (time.time()-t0), end="\t")



            # @TODO:::::
            #nn_bad_where = np.where((nn_ind[:,0]!=np.arange(n_samples)))[0]
            #print(nn_bad_where)
            #print(nn_ind[nn_bad_where,:5])
            #print(X[nn_bad_where,:])
            #assert nn_bad_where.shape[0] == 0

            nn_dist = nn_dist[:,1:].astype(X.dtype, order="C")
            nn_ind  = nn_ind[:,1:].astype(np.intp, order="C")

            if cur_state["M"] > 1:
                # d_core = nn_dist[:,cur_state["M"]-2].astype(X.dtype, order="C")
                raise NotImplementedError("approximate method not implemented yet")

            #t0 = time.time()
            # the fast part:
            mst_dist, mst_ind = internal.mst_from_nn(nn_dist, nn_ind,
                stop_disconnected=False, # TODO: test this!!!!
                stop_inexact=False)
            #print("T=%.3f" % (time.time()-t0), end="\t")

        else: # cur_state["exact"]
            if cur_state["M"] > 1:
                # Genie+HDBSCAN
                # Use sklearn to determine the d_core distance
                nn = sklearn.neighbors.NearestNeighbors(
                    n_neighbors=cur_state["M"]-1,
                    metric=cur_state["affinity"] # supports "precomputed"
                )
                nn_dist, nn_ind = nn.fit(X).kneighbors()
                d_core = nn_dist[:,cur_state["M"]-2].astype(X.dtype, order="C")

            # Use Prim's algorithm to determine the MST
            # w.r.t. the distances computed on the fly
            mst_dist, mst_ind = internal.mst_from_distance(X,
                metric=cur_state["affinity"],
                d_core=d_core
            )

        # apply the Genie+ algorithm (the fast part):
        res = internal.genie_from_mst(mst_dist, mst_ind,
            n_clusters=cur_state["n_clusters"],
            gini_threshold=cur_state["gini_threshold"],
            noise_leaves=(cur_state["M"]>1),
            compute_full_tree=cur_state["compute_full_tree"])

        self.n_clusters_ = res["n_clusters"]
        self.labels_     = res["labels"]
        self.n_samples_  = n_samples
        self.n_features_ = n_features
        self._links_     = res["links"]
        self._iters_     = res["iters"]
        self._mst_dist_  = mst_dist
        self._mst_ind_   = mst_ind
        self._nn_dist_   = nn_dist
        self._nn_ind_    = nn_ind
        self._d_core_    = d_core


        if self.labels_ is not None:
            # postprocess labels, if requested to do so
            if cur_state["M"] == 1 or cur_state["postprocess"] == "none":
                pass
            elif cur_state["postprocess"] == "boundary":
                self.labels_ = internal.merge_boundary_points(mst_ind,
                    self.labels_, nn_ind, cur_state["M"])
            elif cur_state["postprocess"] == "all":
                self.labels_ = internal.merge_noise_points(mst_ind,
                    self.labels_)

        if cur_state["compute_full_tree"]:
            Z = internal.get_linkage_matrix(self._links_,
                self._mst_dist_, self._mst_ind_)
            self.children_    = Z["children"]
            self.distances_   = Z["distances"]
            self.counts_      = Z["counts"]

        return self


    # not needed - inherited from ClusterMixin
    def fit_predict(self, X, y=None):
        """Compute a k-partition and return the predicted labels,
        see fit().


        Parameters
        ----------

        X : ndarray
            see fit()
        y : None
            see fit()


        Returns
        -------

        labels_ : ndarray, shape (n_samples,)
            Predicted labels, representing a partition of X.
            labels_[i] gives the cluster id of the i-th input point.
            negative labels_ correspond to noise points.
            Note that the determined number of clusters
            might be larger than the requested one.
        """
        self.fit(X)
        return self.labels_


    # not needed - inherited from BaseEstimator
    # def __repr__(self):
    #     """
    #     Return repr(self).
    #     """
    #     return "Genie(%s)" % (
    #         ", ".join(["%s=%r"%(k,v) for (k,v) in self.get_params().items()])
    #     )

    #
    # def get_params(self, deep=False):
    #     """
    #     Get the parameters for this estimator.
    #
    #     Parameters:
    #     -----------
    #
    #     deep: bool
    #         Ignored
    #
    #     Returns:
    #     --------
    #
    #     params: dict
    #     """
    #     return dict(
    #         n_clusters = self.__n_clusters,
    #         gini_threshold = self.__gini_threshold,
    #         M = self.__M,
    #         postprocess = self.__postprocess,
    #         n_neighbors = self.__n_neighbors,
    #         **self.__NearestNeighbors_params
    #     )

    # not needed - inherited from BaseEstimator
    # def set_params(self, **params):
    #     """
    #     Set the parameters for this estimator.
    #
    #
    #     Parameters:
    #     -----------
    #
    #     params
    #
    #
    #     Returns:
    #     --------
    #
    #     self
    #     """
    #     ################## @TODO
    #     return self
