`genieclust` Python and R Package
=================================


The *Genie*++ Hierarchical Clustering Algorithm (with Extras)
-------------------------------------------------------------

> **Genie outputs meaningful partitions and is fast even for large data sets.**



Author: [Marek Gagolewski](https://www.gagolewski.com)

Contributors:
[Anna Cena](https://cena.rexamine.com),
[Maciej Bartoszuk](https://bartoszuk.rexamine.com)

The time needed to apply a hierarchical clustering algorithm is most
often dominated by the number of computations of a pairwise
dissimilarity measure. Such a constraint, for larger data sets, puts at
a disadvantage the use of all the classical linkage criteria but the
single linkage one. However, it is known that the single linkage
clustering algorithm is very sensitive to outliers, produces highly
skewed dendrograms and therefore usually does not reflect the true
underlying data structure -- unless the clusters are well-separated.

To overcome its limitations, we proposed a new hierarchical clustering
linkage criterion called Genie. Namely, our algorithm links two clusters
in such a way that a chosen economic inequity measure (here, the Gini index)
of the cluster sizes does not increase drastically above a given threshold.

The algorithm most often outperforms the Ward or average linkage, k-means,
spectral clustering, DBSCAN, Birch and others in terms of the
clustering quality on benchmark data while retaining the single linkage speed.
The algorithm is easily parallelisable and thus may be run on multiple
threads to speed up its execution further on. Its memory overhead is
small: there is no need to precompute the complete distance matrix to
perform the computations in order to obtain a desired clustering.

This package features a new, faster and even more robust implementation of the
original algorithm available on CRAN, see R package
[genie](http://www.gagolewski.com/software/genie/) and the paper:

> Gagolewski M., Bartoszuk M., Cena A., Genie: A new, fast, and
> outlier-resistant hierarchical clustering algorithm, *Information
> Sciences* **363**, 2016, pp. 8-23.
> [doi:10.1016/j.ins.2016.05.003](http://dx.doi.org/10.1016/j.ins.2016.05.003).




Python Package Features
-----------------------

Implemented algorithms include:

-   Genie++ -- a reimplementation of the original Genie algorithm
    (with a `scikit-learn`-compatible interface; Gagolewski et al., 2016)

-   Genie+HDBSCAN\* -- our robustified retake on the HDBSCAN\*
    (Campello et al., 2015) method that detects noise points in data

-   Genie+Ic (GIc) -- Cena's (2018) algorithm to minimise the information
    theoretic criterion discussed by Mueller et al. (2012)

See classes `genieclust.Genie` and `genieclust.GIc`.


Other goodies:

-   `genieclust.inequity` -- Inequity measures (the normalised
    Gini and Bonferroni index)

-   `genieclust.compare_partitions` -- Functions to compare partitions
    (adjusted&unadjusted Rand,
    adjusted&unadjusted Fowlkes-Mallows (FM),
    adjusted&normalised&unadjusted mutual information (MI) scores,
    normalised accuracy and pair sets index (PSI))

-   `genieclust.internal.DisjointSets`, `genieclust.internal.GiniDisjointSets` --
    Union-find data structures (with extensions)

-   `genieclust.plots` -- Useful plotting functions




R Package Features
------------------

The R version of the package features:

-   Partition similarity measures (that can be used as external cluster
    validity scores)

-   Inequity measures



Examples and Tutorials
----------------------

The Python language version of `genieclust` has a familiar `scikit-learn` look-and-feel:

```python
import genieclust
X = ... # some data
g = genieclust.Genie(n_clusters=2)
labels = g.fit_predict(X)
```

TODO: The R version is compatible with `hclust()`...




For more illustrations, use cases and details, make sure to check out:

-   [The Genie Algorithm - Basic Use](https://github.com/gagolews/genieclust/blob/master/tutorials/example_genie_basic.ipynb)
-   [The Genie Algorithm with Noise Points Detection](https://github.com/gagolews/genieclust/blob/master/tutorials/example_noisy.ipynb)
-   **TODO**: GIc Algorithm - Information-Theoretic Clustering
-   [Plotting Dendrograms](https://github.com/gagolews/genieclust/blob/master/tutorials/dendrogram.md)
-   [Comparing Different Hierarchical Linkage Methods on Toy Datasets - A `scikit-learn` Example](https://github.com/gagolews/genieclust/blob/master/tutorials/sklearn_toy_example.md)
-   [Auxiliary Plotting Functions](https://github.com/gagolews/genieclust/blob/master/tutorials/plots.md)


Installation
------------

> *This package is in an alpha-stage (development and testing is Linux-only).*

The package requires Python 3.6+ together with `cython` as well as
`numpy`, `scipy`, `matplotlib` and `sklearn`.

Optional dependencies: `rpy2`, `faiss` (e.g. `faiss-cpu`), `mlpack`.


To build and install the most recent development version:

```bash
git clone https://github.com/gagolews/genieclust.git
cd genieclust
python3 setup.py install --user
```

To support parallelised computations, build with OpenMP support (for gcc/clang):

```bash
CPPFLAGS="-fopenmp -DNDEBUG" LDFLAGS="-fopenmp" python3 setup.py install --user
```




**TODO**: Windows builds

**TODO**: OS X builds

**TODO** To install via `pip` (the current version is a little outdated,
see [PyPI](https://pypi.org/project/genieclust/)):

```bash
pip3 install genieclust --user # or sudo pip3 install genieclust
```


TODO: R version



License
-------

Copyright (C) 2018-2020 Marek Gagolewski (https://www.gagolewski.com)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License
Version 3, 19 November 2007, published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License Version 3 for more details.
You should have received a copy of the License along with this program.
If not, see (https://www.gnu.org/licenses/).


---

The file `src/c_scipy_rectangular_lsap.h` is adapted from the `scipy` project
(https://scipy.org/scipylib/), source:
`/scipy/optimize/rectangular_lsap/rectangular_lsap.cpp`.
Author: PM Larsen. Distributed under the BSD-3-Clause license.





References
----------

Gagolewski M., Bartoszuk M., Cena A.,
Genie: A new, fast, and outlier-resistant hierarchical clustering algorithm,
*Information Sciences* **363**, 2016, pp. 8-23.
doi:10.1016/j.ins.2016.05.003

Cena A., Gagolewski M.,
Genie+OWA: Robustifying Hierarchical Clustering with OWA-based Linkages,
*Information Sciences*, 2020,
in press. doi:10.1016/j.ins.2020.02.025

Cena A.,
Adaptive hierarchical clustering algorithms based on data aggregation methods,
PhD Thesis, Systems Research Institute, Polish Academy of Sciences, 2018.

Campello R., Moulavi D., Zimek A., Sander J.,
Hierarchical density estimates for data clustering, visualization,
and outlier detection,
*ACM Transactions on Knowledge Discovery from Data* **10**(1), 2015, 5:1–5:51.
doi:10.1145/2733381.

Crouse D.F., On implementing 2D rectangular assignment algorithms,
*IEEE Transactions on Aerospace and Electronic Systems* **52**(4), 2016,
pp. 1679-1696, doi:10.1109/TAES.2016.140952.

Mueller A., Nowozin S., Lampert C.H.,
Information Theoretic Clustering using Minimum Spanning Trees,
*DAGM-OAGM* 2012.

Jarník V., O jistém problému minimálním,
*Práce Moravské Přírodovědecké Společnosti* **6**, 1930, pp. 57–63.

Olson C.F., Parallel algorithms for hierarchical clustering,
*Parallel Comput.* **21**, 1995, pp. 1313–1325.

Prim R., Shortest connection networks and some generalizations,
*Bell Syst. Tech. J.* **36**, 1957, pp. 1389–1401.

Hubert L., Arabie P., Comparing Partitions,
*Journal of Classification* **2**(1), 1985, pp. 193-218.

Rezaei M., Franti P., Set matching measures for external cluster validity,
*IEEE Transactions on Knowledge and Data Mining* **28**(8), 2016, pp. 2173-2186,
doi:10.1109/TKDE.2016.2551240

Vinh N.X., Epps J., Bailey J.,
Information theoretic measures for clusterings comparison:
Variants, properties, normalization and correction for chance,
*Journal of Machine Learning Research* **11**, 2010, pp. 2837-2854.
