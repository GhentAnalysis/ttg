''' 
Multi-dimensional polonomial parametrization.

Given a list of values w for data-points (c1, ..., cN) in the form  
[ (c1, ..., cN), ... ]
a polyonomial parametrization
w(c) = w_0 + w_i c_i + w_ij c_ij + ... 
is constructed. The w_0, w_i, w_ij, ... are defined by the chi2 minimum.
The instance is initialized with the base_point coordinates in parameter space.
The parametrization coefficients are evaluated for a given set of weights corresponding to the base_points.

Math:

Write a polyonimal parametrization as w(c) = w_0 + w_i c_i + w_ij c_ij + w_ijk c_ijk + ...
where ijkl... is summed over all combinations with repetitions.
Define the notation: < ijk > = 1/N sum_data( c_i*c_j*c_k ) etc.
Now differentiate chi2 = <(w - wEXT)**2> wrt to the w_0, w_i, ...
This gives equations of the form
< ( w - wEXT ) >  = 0    
< ( w - wEXT ) m >  = 0  
< ( w - wEXT ) mn >  = 0 
... etc.

up to 2nd order:
1. w_0      + w_i <i>   + w_ij <ij>   - < wEXT >    = 0 
2. w_0 <m>  + w_i <im>  + w_ij <ijm>  - < wEXT m >  = 0
3. w_0 <mn> + w_i <imn> + w_ij <ijmn> - < wEXT mn > = 0

up to 4nd order:
1. < ( w - wEXT ) >  = 0         w_0        + w_i <i>     + w_ij <ij>     + w_ijk <ijk>     + w_ijkl <ijkl>     = <wEXT >
2. < ( w - wEXT ) m >  = 0       w_0 <m>    + w_i <im>    + w_ij <ijm>    + w_ijk <ijkm>    + w_ijkl <ijklm>    = <wEXT m>
3. < ( w - wEXT ) mn >  = 0      w_0 <mn>   + w_i <imn>   + w_ij <ijmn>   + w_ijk <ijkmn>   + w_ijkl <ijklmn>   = <wEXT mn>
4. < ( w - wEXT ) mno >  = 0     w_0 <mnk>  + w_i <imnk>  + w_ij <ijmnk>  + w_ijk <ijkmno>  + w_ijkl <ijklmno>  = <wEXT mno>
5. < ( w - wEXT ) mnop >  = 0    w_0 <mnkl> + w_i <imnkl> + w_ij <ijmnkl> + w_ijk <ijkmnop> + w_ijkl <ijklmnop> = <wEXT mnop>

The class implements the general case of a n-th order polynomial.
'''

# Logger
import logging
logger = logging.getLogger(__name__)

# General imports
import operator
import numpy as np
import scipy.special
import itertools

# Helpers
from helpers import timeit as timeit

class HyperPoly:

    @staticmethod
    def get_ndof( nvar, order ):
        ''' Compute the number of d.o.f. of the polynomial by summing up o in the formula for combinations with repetitions of order o in nvar variables'''
        return sum( [ int(scipy.special.binom(nvar + o - 1, o)) for o in xrange(order+1) ] )

    def __init__( self, order ):
        self.order       = order
        self.initialized = False

    # Initialize with data ( c1, ..., cN )
    def initialize( self, param_points, ref_point = None):

        # Let's not allow re-initialization.
        if self.initialized:
            raise RuntimeError( "Already initialized!" )

        # Make sure dimensionality of data is consistent
        if not len(set( map( len, param_points ) )) == 1:
            raise ValueError( "'param_points' are not consistent. Need a list of iterables of the same size." )

        # Length of the dataset
        self.N   = len( param_points )
        # Coordinates
        self.param_points = param_points 
        # Number of variables
        self.nvar = len( param_points[0] ) 
        # Reference point
        self.ref_point = ref_point if ref_point is not None else tuple([0 for var in xrange(self.nvar)])
        # Check reference point
        if len(self.ref_point)!=self.nvar:
            logger.error('Reference point has length %i but should have length %i', len(self.ref_point), self.nvar )
            raise RuntimeError

        logger.debug( "Make parametrization of polynomial in %i variables to order %i" % (self.nvar, self.order ) )

        # We have Binomial( n + o - 1, o ) coefficients for n variables at order o
        # ncoeff = {o:int(scipy.special.binom(self.nvar + o - 1, o)) for o in xrange(order+1)}
        # Total number of DOF
        self.ndof = HyperPoly.get_ndof( self.nvar, self.order )
        # Order of combinations (with replacements) and ascending in 'order'
        self.combination  = {}
        counter = 0
        for o in xrange(self.order+1):
            for comb in itertools.combinations_with_replacement( xrange(self.nvar), o ):
                self.combination[counter] = comb
                counter += 1

        # Now we solve A.x = b for a system of dimension DOF
        # Fill A
        A = np.empty( [self.ndof, self.ndof ] )
        for d in range(self.ndof):
            for e in range(self.ndof):
                if d > e:
                    A[d][e] = A[e][d]
                else:
                    A[d][e] = self.expectation(self.combination[d] + self.combination[e]) 

        # Invert (Yes, n^3. But ... only the inhomongeneity depends on the weights, so Ainv is universal for the sample!)

        self.Ainv = timeit(np.linalg.inv)(A)
        self.initialized = True

    def get_parametrization( self, weights ): 
        ''' Obtain the parametrization for given weights
        '''
        if len(weights)!=self.N:
            raise ValueError( "Need %i weights that correspond to the same number of param_points. Got %i." % (self.N, len(weights)) )
        b = np.array( [ self.wEXT_expectation( weights, self.combination[d] ) for d in range(self.ndof) ] )
        return np.dot(self.Ainv, b)

    def wEXT_expectation(self, weights, combination ):
        ''' Compute <wEXT ijk...> = 1/Nmeas Sum_meas( wEXT_meas*i_meas*j_meas*k_meas... )
        '''
        return sum( [ weights[n]*np.prod( [ (self.param_points[n][elem]-self.ref_point[elem]) for elem in combination ] ) for n in xrange(self.N) ] ) / float(self.N)

    def expectation(self, combination ):
        ''' Compute <wEXT ijk...> = 1/Nmeas Sum_meas( i_meas*j_meas*k_meas... )
        '''
        return sum( [ np.prod( [ (self.param_points[n][elem] - self.ref_point[elem]) for elem in combination ] ) for n in range(self.N) ]) / float(self.N)

    def eval( self, coefficients, *point ):
        ''' Evaluate parametrization
        '''
        if not len(point) == self.nvar:
            raise ValueError( "Polynomial degree is %i. Got %i arguments." % (self.nvar, len(point) ) )
#        return sum( ( coefficients[n] - self.reference_coefficients[n] ) * np.prod( [ point[elem] for elem in self.combination[n] ] ) for n in range(self.ndof) ) 
        return sum( coefficients[n] * np.prod( [ (point[elem] - self.ref_point[elem]) for elem in self.combination[n] ] ) for n in range(self.ndof) ) 
   
    def chi2( self, coefficients, weights):
        return sum( [ (self.eval(coefficients, *self.param_points[n]) - weights[n])**2 for n in range(self.N) ] )
    
    def chi2_ndof( self, coefficients, weights):
        return self.chi2( coefficients, weights )/float(self.ndof)

    min_abs_float = 1e-10
    def root_func_string(self, coefficients):
        substrings = []
        for n in range(self.ndof):
            if True:
#            if abs(coefficients[n])>self.min_abs_float:
                sub_substring = []
                if True:
#                if abs(1-coefficients[n])>self.min_abs_float:
                    sub_substring.append( ('%f'%coefficients[n]).rstrip('0') )
                for var in range(self.nvar):
                    power = self.combination[n].count( var )
                    if power>0:
                        sub_substring.append( "(x%i-%f)" % (var, self.ref_point[var]) if power==1 else "(x%i-%f)**%i" % (var, self.ref_point[var], power)  )
##                        sub_substring.append( "x%i" % (var) if power==1 else "x%i**%i" % (var, power)  )
##                        if abs(self.ref_point[var])>self.min_abs_float:
##                            sub_substring.append( "(x%i-%f)" % (var, self.ref_point[var]) if power==1 else "(x%i-%f)**%i" % (var, self.ref_point[var], power)  )
##                        else:
##                            sub_substring.append( "x%i" % (var) if power==1 else "x%i**%i" % (var, power)  )
                substrings.append( "*".join(sub_substring) ) 
        return  ( "+".join( filter( lambda s: len(s)>0, substrings) ) ).replace("+-","-")

if __name__ == "__main__":

    # 3rd order parametrization
    def f1(x,y,z):
        return (x-z)**3+(y-2)**2
    ref_point = (0,3,0)

    p = HyperPoly(3)

    param_points = [ (x,y,z) for x in range(-3,3) for y in range(-3,3) for z in range( -3,3)]
    p.initialize( param_points, ref_point)
    
    weights     = [ f1(*point) for point in param_points]
    coeff = p.get_parametrization( weights )

    print "len param_points", len(param_points)
    print "coeff", coeff
    print "chi2/ndof", p.chi2_ndof( coeff, weights)
    print "ndof", p.ndof
    print "String:", p.root_func_string(coeff)

    #def f2(x,y,z):
    #    return (x-z)**3 + y
    #weights     = [ f2(*point) for point in param_points]
    #coeff = p.get_parametrization( weights )

    #print "chi2/ndof", p.chi2_ndof(coeff, weights)
    #print "String:", p.root_func_string(coeff)
