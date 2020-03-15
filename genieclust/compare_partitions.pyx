# distutils: language=c++
# cython: boundscheck=False
# cython: cdivision=True
# cython: nonecheck=False
# cython: wraparound=False
# cython: language_level=3


"""
Adjusted- and Nonadjusted Rand Score,
Adjusted- and Nonadjusted Fowlkes-Mallows Score
(for vectors of `small' ints)

See Hubert L., Arabie P., Comparing Partitions,
    Journal of Classification 2(1), 1985, 193-218


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


cimport numpy as np
import numpy as np
from . cimport c_compare_partitions


ctypedef fused intT:
    int
    long
    long long
    ssize_t


cpdef np.ndarray[ssize_t,ndim=2] normalize_confusion_matrix(ssize_t[:, ::1] C):
    """
    Applies pivoting to a given confusion matrix.
    Nice if C actually summarises clustering results,
    where actual labels do not matter.

    Parameters:
    ----------

    C : ndarray, shape (kx,ky)
        a c_contiguous confusion matrix


    Returns:
    -------

    C_normalized: ndarray, shape(kx,ky)
    """
    cdef np.ndarray[ssize_t,ndim=2] C_normalized = np.array(C, dtype=np.intp)
    cdef ssize_t xc = C_normalized.shape[0]
    cdef ssize_t yc = C_normalized.shape[1]
    c_compare_partitions.Capply_pivoting(&C_normalized[0,0], xc, yc)
    return C_normalized



cpdef np.ndarray[ssize_t,ndim=2] confusion_matrix(intT[:] x, intT[:] y):
    """
    Computes the confusion matrix (as a dense matrix)


    Parameters:
    ----------

    x, y : ndarray, shape (n,)
        two small-int vectors of the same lengths


    Returns:
    -------

    C : ndarray, shape (kx, ky)
        a confusion matrix
    """
    cdef ssize_t n = x.shape[0]
    if n != y.shape[0]: raise ValueError("incompatible lengths")
    cdef ssize_t CONFUSION_MATRIX_MAXSIZE = 10000

    cdef np.ndarray[ssize_t] _x = np.array(x, dtype=np.intp)
    cdef ssize_t xmin, xmax
    c_compare_partitions.Cminmax(<ssize_t*>(&_x[0]), n, <ssize_t*>(&xmin), <ssize_t*>(&xmax))
    cdef ssize_t xc = (xmax-xmin+1)

    cdef np.ndarray[ssize_t] _y = np.array(y, dtype=np.intp)
    cdef ssize_t ymin, ymax
    c_compare_partitions.Cminmax(<ssize_t*>(&_y[0]), n, <ssize_t*>(&ymin), <ssize_t*>(&ymax))
    cdef ssize_t yc = (ymax-ymin+1)

    if xc*yc > CONFUSION_MATRIX_MAXSIZE:
        raise ValueError("CONFUSION_MATRIX_MAXSIZE exceeded")

    cdef np.ndarray[ssize_t,ndim=2] C = np.empty((xc, yc), dtype=np.intp)
    c_compare_partitions.Ccontingency_table(&C[0,0], xc, yc, xmin, ymin, &_x[0], &_y[0], n)
    return C



cpdef np.ndarray[ssize_t,ndim=2] normalized_confusion_matrix(intT[:] x, intT[:] y):
    """
    Computes the confusion matrix between x and y
    and applies pivoting. Nice for summarising clustering results,
    where actual labels do not matter.


    Parameters:
    ----------

    x, y : ndarray, shape (n,)
        two small-int vectors of the same lengths, representing
        two k-partitions of the same set


    Returns:
    -------

    C : ndarray, shape (kx, ky)
        a confusion matrix
    """
    cdef np.ndarray[ssize_t,ndim=2] C = confusion_matrix(x, y)
    return normalize_confusion_matrix(C)



cpdef c_compare_partitions.CComparePartitionsResult compare_partitions(ssize_t[:,::1] C):
    """
    Computes the adjusted and nonadjusted Rand- and FM scores
    based on a given confusion matrix.

    See Hubert L., Arabie P., Comparing Partitions,
       Journal of Classification 2(1), 1985, 193-218, esp. Eqs. (2) and (4)


    Parameters:
    ----------

    C : ndarray, shape (kx,ky)
        a confusion matrix

    Returns:
    -------

    scores : dict
        a dictionary with keys 'ar', 'r', 'afm', 'fm', giving
        the adjusted Rand, Rand, adjusted Fowlkes-Mallows, and
        Fowlkes-Mallows scores, respectively.
    """
    cdef ssize_t xc = C.shape[0]
    cdef ssize_t yc = C.shape[1]
    return c_compare_partitions.Ccompare_partitions(&C[0,0], xc, yc)


cpdef c_compare_partitions.CComparePartitionsResult compare_partitions2(intT[:] x, intT[:] y):
    """
    Calls compare_partitions(confusion_matrix(x, y)).


    Parameters:
    ----------

    x, y : ndarray, shape (n,)
        two small-int vectors of the same lengths, representing
        two k-partitions of the same set

    Returns:
    -------

    scores : dict
        a dictionary with keys 'ar', 'r', 'afm', 'fm', giving
        the adjusted Rand, Rand, adjusted Fowlkes-Mallows, and
        Fowlkes-Mallows scores, respectively.
    """
    return compare_partitions(confusion_matrix(x, y))


cpdef double adjusted_rand_score(intT[:] x, intT[:] y):
    """
    The Rand index adjusted for chance.

    See Hubert L., Arabie P., Comparing Partitions,
    Journal of Classification 2(1), 1985, 193-218


    Parameters:
    ----------

    x, y : ndarray, shape (n,)
        two small-int vectors of the same lengths, representing
        two k-partitions of the same set


    Returns:
    -------

    score : double
        partition similarity measure
    """

    return compare_partitions(confusion_matrix(x, y)).ar


cpdef double rand_score(intT[:] x, intT[:] y):
    """
    The original Rand index (not adjusted for chance),
    yielding the `probability' of agreement between the two partitions

    See Hubert L., Arabie P., Comparing Partitions,
    Journal of Classification 2(1), 1985, 193-218


    Parameters:
    ----------

    x, y : ndarray, shape (n,)
        two small-int vectors of the same lengths, representing
        two k-partitions of the same set


    Returns:
    -------

    score : double
        partition similarity measure
    """

    return compare_partitions(confusion_matrix(x, y)).r


cpdef double adjusted_fm_score(intT[:] x, intT[:] y):
    """
    The Fowlkes-Mallows index adjusted for chance,

    See Eqs. (2) and (4)  in Hubert L., Arabie P., Comparing Partitions,
    Journal of Classification 2(1), 1985, 193-218

    Parameters:
    ----------

    x, y : ndarray, shape (n,)
        two small-int vectors of the same lengths, representing
        two k-partitions of the same set


    Returns:

    score : double
        partition similarity measure
    """

    return compare_partitions(confusion_matrix(x, y)).afm


cpdef double fm_score(intT[:] x, intT[:] y):
    """
    The original Fowlkes-Mallows index (not adjusted for chance)

    See Hubert L., Arabie P., Comparing Partitions,
    Journal of Classification 2(1), 1985, 193-218

    Parameters:
    ----------

    x, y : ndarray, shape (n,)
        two small-int vectors of the same lengths, representing
        two k-partitions of the same set


    Returns:
    -------

    score : double
        partition similarity measure
    """

    return compare_partitions(confusion_matrix(x, y)).fm
