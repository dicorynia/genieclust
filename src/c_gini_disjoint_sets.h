/*  class CGiniDisjointSets
 *
 *  Copyright (C) 2018-2020 Marek Gagolewski (https://www.gagolewski.com)
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Affero General Public License
 *  Version 3, 19 November 2007, published by the Free Software Foundation.
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 *  GNU Affero General Public License Version 3 for more details.
 *  You should have received a copy of the License along with this program.
 *  If not, see <https://www.gnu.org/licenses/>.
 */




#ifndef __c_gini_disjoint_sets_h
#define __c_gini_disjoint_sets_h

#include "c_common.h"
#include "c_disjoint_sets.h"
#include "c_int_dict.h"



/*! "Augmented" Disjoint Sets (Union-Find) Data Structure
 *
 *  A class to represent partitions of the set {0,1,...,n-1} for any n.
 *
 *  The class allows to compute the normalised Gini index of the distribution
 *  of subset sizes, i.e.,
 *  \[
 *   G(x_1,\dots,x_k) = \frac{
 *   \sum_{i=1}^{n-1} \sum_{j=i+1}^n |x_i-x_j|
 *   }{
 *   (n-1) \sum_{i=1}^n x_i
 *   }.
 *  \]
 *
 *  The merge() operation, which also recomputes the Gini index,
 *  has O(sqrt n) time complexity.
 *
 *  For a use case, see: Gagolewski M., Bartoszuk M., Cena A.,
 *  Genie: A new, fast, and outlier-resistant hierarchical clustering algorithm,
 *  Information Sciences 363, 2016, pp. 8-23. doi:10.1016/j.ins.2016.05.003
 */
class CGiniDisjointSets : public CDisjointSets{

protected:
    std::vector<ssize_t> cnt;  //!< cnt[find(x)] is the size of the relevant subset

    CIntDict<ssize_t> number_of_size; /*!< number_of_size[i] gives the number
        * of subsets of size i (there are at most sqrt(n) possible
        * non-zero elements) */

    double gini;   //!< the Gini index of the current subset sizes


public:
    /*! Starts with a "weak" partition {  {0}, {1}, ..., {n-1}  },
     *  i.e., n singletons.
     *
     *  @param n number of elements, n>=0.
     */
    CGiniDisjointSets(ssize_t n) :
        CDisjointSets(n),
        cnt(n, 1),           // each cluster is of size 1
        number_of_size(n+1)
    {
        if (n>0) number_of_size[1] = n; // there are n clusters of size 1
        gini = 0.0;   // a perfectly balanced cluster size distribution
    }


    /*! A nullary constructor allows Cython to allocate
     *  the instances on the stack.  Do not use otherwise.
    */
    CGiniDisjointSets() : CGiniDisjointSets(0) { }


    /*! Returns the Gini index of the distribution of subsets' sizes.
     *
     *  Run time: O(1), as the Gini index is updated during a call
     *  to merge().
     */
    double get_gini() const { return this->gini; }


    /*! Returns the size of the smallest subset.
     *
     *  Run time: O(1).
     */
    ssize_t get_smallest_count() const {
        return number_of_size.get_key_min(); /*this->tab_head;*/
    }


    /*! Returns the size of the subset containing x.
     *
     * Run time: the cost of find(x)
     */
    ssize_t get_count(ssize_t x) {
        x = this->find(x);
        return this->cnt[x];
    }


    /*! Merges the sets containing x and y in {0,...,n-1}.
     *
     *  Let px be the parent id of x, and py be the parent id of y.
     *  If px < py, then the new parent id of py will be set to py.
     *  Otherwise, px will have py as its parent.
     *
     *  If x and y are members of the same subset,
     *  an exception is thrown.
     *
     *  @return the id of the parent of x or y, whichever is smaller.
     *
     *  @param x a value in {0,...,n-1}
     *  @param y a value in {0,...,n-1}
     *
     *  Update time: pessimistically O(sqrt(n)).
     */
    virtual ssize_t merge(ssize_t x, ssize_t y)
    { // well, union is a reserved C++ keyword :)
        // the ordinary DisjointSet's merge:
        x = this->find(x); // includes a range check for x
        y = this->find(y); // includes a range check for y
        if (x == y) throw std::invalid_argument("find(x) == find(y)");
        if (y < x) std::swap(x, y);

        this->par[y] = x; // update the parent of y
        this->k -= 1;     // decrease the subset count

        // update the counts
        ssize_t size1 = this->cnt[x];
        ssize_t size2 = this->cnt[y];
        ssize_t size12 = size1+size2;
        this->cnt[x] += this->cnt[y]; // cluster x has more elements now
        this->cnt[y] = 0;             // cluster y, well, cleaning up

        //GENIECLUST_ASSERT(number_of_size.at(size1)>0);
        number_of_size[size1]  -= 1; // one cluster of size1 is no more
        //GENIECLUST_ASSERT(number_of_size.at(size2)>0);
        number_of_size[size2]  -= 1; // one cluster of size2 is an ex-cluster

        // get rid of size1 and size2, if necessary
        if (size2 < size1) std::swap(size1, size2);

        if (number_of_size.at(size1) <= 0)
            number_of_size.erase(size1);  // fast

        if (size1 != size2 && number_of_size.at(size2) <= 0)
            number_of_size.erase(size2);  // fast

        if (number_of_size.count(size12) == 0)
            number_of_size[size12] = 1;   // might be O(sqrt(n))
        else
            number_of_size[size12] += 1; // long live cluster of size1+2

        // re-compute the normalized Gini index
        // based on a formula given in [TODO:derive the formula nicely]
        gini = 0.0;
        if (number_of_size.size() > 1) { // otherwise all clusters are of identical sizes
            ssize_t v = number_of_size.get_key_min();
            ssize_t i = 0;
            while (v != number_of_size.get_key_max()) {
                ssize_t w = v;                       // previous v
                v = number_of_size.get_key_next(v);  // next v
                i += number_of_size[w];              // cumulative counts
                gini += ((double)v-w)*i*((double)k-i);
            }
            gini /= (double)(n*(k-1.0)); // this is the normalised Gini index
            if (gini > 1.0) gini = 1.0; // account for round-off errors
            if (gini < 0.0) gini = 0.0;
        }

        // all done
        return x;
    }


    /*! Generates an array of subsets' sizes.
     *  The resulting vector is ordered nondecreasingly.
     *
     *  Run time: O(k), where k is the current number of subsets.
     *
     *  @param res [out] c_contiguous array of length k
     */
    void get_counts(ssize_t* res) {
        ssize_t i = 0;
        for (CIntDict<ssize_t>::iterator it = number_of_size.begin();
             it != number_of_size.end(); ++it)
        {
            // add this->tab[v] times v
            for (ssize_t j=0; j<number_of_size[*it]; ++j) {
                GENIECLUST_ASSERT(i<k);
                res[i++] = *it;
            }
        }
    }

};

#endif
