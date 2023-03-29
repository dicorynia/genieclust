/*  Internal cluster validity indices
 *
 *  Code originally contributed in <https://github.com/gagolews/optim_cvi>,
 *  see https://doi.org/10.1016/j.ins.2021.10.004.
 *  Copyleft (C) 2020, Maciej Bartoszuk <http://bartoszuk.rexamine.com>
 *
 *  For the 'genieclust' version:
 *  Copyleft (C) 2020-2023, Marek Gagolewski <https://www.gagolewski.com>
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Affero General Public License
 *  Version 3, 19 November 2007, published by the Free Software Foundation.
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 *  GNU Affero General Public License Version 3 for more details.
 *  You should have received a copy of the License along with this program.
 *  If this is not the case, refer to <https://www.gnu.org/licenses/>.
 */

#ifndef __CVI_GENERALIZED_DUNN_UPPERCASE_D3_H
#define __CVI_GENERALIZED_DUNN_UPPERCASE_D3_H

#include "cvi.h"
#include "cvi_generalized_dunn_delta.h"

class UppercaseDelta3 : public UppercaseDelta
{
protected:
    std::vector<double> dist_sums; ///< sum of points distances to centroid:
    std::vector<double> last_dist_sums;      ///< for undo()
    bool last_chg; ///< for undo() (was dist changed at all?)
    Py_ssize_t cluster1;
    Py_ssize_t cluster2;
public:
    UppercaseDelta3(
        EuclideanDistance& D,
        const CMatrix<FLOAT_T>& X,
        std::vector<Py_ssize_t>& L,
        std::vector<size_t>& count,
        size_t K,
        size_t n,
        size_t d,
        CMatrix<FLOAT_T>* centroids=nullptr
        )
    : UppercaseDelta(D,X,L,count,K,n,d,centroids),
    dist_sums(K),
    last_dist_sums(K),
    last_chg(false)
    { }
    virtual void before_modify(size_t i, Py_ssize_t j) {
        last_chg = true;
        for (size_t u=0; u<K; ++u) {
                last_dist_sums[u] = dist_sums[u];
        }

        cluster1 = L[i];

        // Py_ssize_t cluster_index = L[i];
        // FLOAT_T act = 0.0;
        // for (size_t u=0; u<d; ++u) {
        //     act += square((*centroids)(cluster_index, u) - X(i, u));
        // }
        // FLOAT_T d = sqrt(act);
        // dist_sums[cluster_index] -= d;
    }

    virtual void after_modify(size_t i, Py_ssize_t j) {
        // Py_ssize_t cluster_index = L[i];
        // FLOAT_T act = 0.0;
        // for (size_t u=0; u<d; ++u) {
        //     act += square((*centroids)(cluster_index, u) - X(i, u));
        // }
        // FLOAT_T d = sqrt(act);
        // dist_sums[cluster_index] += d;

        cluster2 = L[i];

        dist_sums[cluster1] = 0;
        dist_sums[cluster2] = 0;

        for (size_t i=0; i<n; ++i) {
            Py_ssize_t cluster_index = L[i];
            if (cluster_index == cluster1 || cluster_index == cluster2) {
                FLOAT_T act = 0.0;
                for (size_t u=0; u<d; ++u) {
                    act += square((*centroids)(cluster_index, u) - X(i, u));
                }
                FLOAT_T d = sqrt(act);
                dist_sums[cluster_index] += d;
            }
        }

    }

    virtual void undo(){
        if (last_chg) {
            for (size_t i=0; i<K; ++i) {
                dist_sums[i] = last_dist_sums[i];
            }
        }
    }

    virtual void recompute_all(){
        // Rcpp::Rcout << "before fill"<< std::endl;
        std::fill(dist_sums.begin(), dist_sums.end(), 0);
        // Rcpp::Rcout << "after fill"<< std::endl;

        // Rcpp::Rcout << "centroids = " << centroids << std::endl;
        // Rcpp::Rcout << "centroids[0][0] = " << (*centroids)(0,0) << std::endl;

        for (size_t i=0; i<n; ++i) {
            Py_ssize_t cluster_index = L[i];
            FLOAT_T act = 0.0;
            for (size_t u=0; u<d; ++u) {
                act += square((*centroids)(cluster_index, u) - X(i, u));
            }
            FLOAT_T d = sqrt(act);
            dist_sums[cluster_index] += d;
        }
    }

    virtual FLOAT_T compute(size_t k){
        return 2.0*(dist_sums[k])/(count[k]);
    }
};


class UppercaseDelta3Factory : public UppercaseDeltaFactory
{
public:
    virtual bool IsCentroidNeeded() { return true; }

    virtual UppercaseDelta* create(EuclideanDistance& D,
           const CMatrix<FLOAT_T>& X,
           std::vector<Py_ssize_t>& L,
           std::vector<size_t>& count,
           size_t K,
           size_t n,
           size_t d,
           CMatrix<FLOAT_T>* centroids=nullptr) {
               return new UppercaseDelta3(D, X, L, count, K, n, d, centroids);
           }
};

#endif
