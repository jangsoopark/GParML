# Copyright I. Nabney, N.Lawrence and James Hensman (1996 - 2012)
'''
Adapted version of SCG that makes use of a single objective_and_gradient function
for cases when it is cheaper to evaluate both together
'''
# Scaled Conjuagte Gradients, originally in Matlab as part of the Netlab toolbox by I. Nabney, converted to python N. Lawrence and given a pythonic interface by James Hensman

#      THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT
#      HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
#      EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
#      NOT LIMITED TO, THE IMPLIED WARRANTIES OF
#      MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#      PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
#      REGENTS OR CONTRIBUTORS BE LIABLE FOR ANY
#      DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#      EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#      (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
#      OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#      DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
#      HOWEVER CAUSED AND ON ANY THEORY OF
#      LIABILITY, WHETHER IN CONTRACT, STRICT
#      LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#      OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#      OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#      POSSIBILITY OF SUCH DAMAGE.


import numpy as np
import sys
from numpy.linalg.linalg import LinAlgError
import warnings
debug = False

def print_out(len_maxiters, display, fnow, current_grad, beta, iteration):
    if display:
        print 
        print '\r',
        print '{0:>0{mi}g}  {1:> 12e}  {2:> 12e}  {3:> 12e}'.format(iteration, float(fnow), float(beta), float(current_grad), mi=len_maxiters), # print 'Iteration:', iteration, ' Objective:', fnow, '  Scale:', beta, '\r',
        print 
        sys.stdout.flush()

_fail_count = 0
_allowed_failures = 100
def safe_f_and_grad_f(f_and_gradf, x, iteration=0, *optargs):
    '''
    Calls f and gradf and returns inf for f in case of warnings / assertion errors and so on.
    The returned gradf in that case is 0, which screws up SCG's momentum, so a re-start should be done
    '''
    global _fail_count, _allowed_failures
    try:
        [f, gradf] = f_and_gradf(x, iteration, *optargs)
        _fail_count = 0
    except (LinAlgError, ZeroDivisionError, ValueError, Warning, AssertionError) as e:
        if _fail_count >= _allowed_failures:
            print 'Too many errors...'
            raise e
        _fail_count += 1
        print 
        print '\tIncreasing failed count: ' + str(_fail_count)
        print 
        #print 'x catch:'
        #print x
        #print 
        #[f, gradf] = f_and_gradf(x, iteration, *optargs)
        #print 'gradf catch:'
        #print gradf
        #print 
        f = np.inf
        gradf = np.ones(x.shape)
    return f, gradf

def SCG_adapted(f_and_gradf, local_optimisation, x, optargs=(), maxiters=500, max_f_eval=500, display=True, xtol=None, ftol=None, gtol=None):
    """
    Optimisation through Scaled Conjugate Gradients (SCG)

    f: the objective function
    gradf : the gradient function (should return a 1D np.ndarray)
    x : the initial condition

    Returns
    x the optimal value for x
    flog : a list of all the objective values
    function_eval number of fn evaluations
    status: string describing convergence status
    """
    if xtol is None:
        xtol = 1e-6
    if ftol is None:
        ftol = 1e-6
    if gtol is None:
        gtol = 1e-5
    sigma0 = 1.0e-8
    f_gradf = safe_f_and_grad_f(f_and_gradf, x, iteration=0, *optargs)
    fold = f_gradf[0] # Initial function value.
    function_eval = 1
    fnow = fold
    gradnew = f_gradf[1] # Initial gradient.
    current_grad = np.dot(gradnew, gradnew)
    gradold = gradnew.copy()
    d = -gradnew # Initial search direction.
    success = True # Force calculation of directional derivs.
    nsuccess = 0 # nsuccess counts number of successes.
    beta = 1.0 # Initial scale parameter.
    betamin = 1.0e-60 # Lower bound on scale.
    betamax = 1.0e100 # Upper bound on scale.
    status = "Not converged"

    flog = [fold]

    iteration = 0

    len_maxiters = len(str(maxiters))
    if display:
        print ' {0:{mi}s}   {1:11s}    {2:11s}    {3:11s}'.format("I", "F", "Scale", "|g|", mi=len_maxiters)

    # Main optimization loop.
    print 'Starting optimisation for ' + str(maxiters) + ' iterations'
    if debug:
        print 'x'
        print x
    while iteration < maxiters:

        # Calculate first and second directional derivatives.
        if success:
            mu = np.dot(d, gradnew)
            if mu >= 0:
                d = -gradnew
                mu = np.dot(d, gradnew)
            kappa = np.dot(d, d)
            sigma = sigma0 / np.sqrt(kappa)
            xplus = x + sigma * d
            gplus = safe_f_and_grad_f(f_and_gradf, xplus, iteration=-1, *optargs)[1]
            theta = np.dot(d, (gplus - gradnew)) / sigma
            if debug:
                print 'kappa'
                print kappa
                print 'xplus'
                print xplus
                print 'gradnew'
                print gradnew
                print 'gplus'
                print gplus
                print 'sigma'
                print sigma
                print 'theta'
                print theta

        # Increase effective curvature and evaluate step size alpha.
        delta = theta + beta * kappa
        if delta <= 0:
            delta = beta * kappa
            beta = beta - theta / kappa

        alpha = -mu / delta

        # Calculate the comparison ratio.
        xnew = x + alpha * d
        f_gradf = safe_f_and_grad_f(f_and_gradf, xnew, iteration=iteration + 1, *optargs)
        fnew = f_gradf[0]
        function_eval += 1

        if function_eval >= max_f_eval:
            status = "Maximum number of function evaluations exceeded"
            break
            #return x, flog, function_eval, status

        Delta = 2.*(fnew - fold) / (alpha * mu)
        if Delta >= 0.:
            success = True
            nsuccess += 1
            x = xnew
            fnow = fnew
        else:
            success = False
            fnow = fold

        if debug:
            print 'd'
            print d
            print 'alpha'
            print alpha
            print 'xnew'
            print xnew
            print 
            print 'mu'
            print mu
            print 'fnew'
            print fnew
            print 'fold'
            print fold
            print 'Delta'
            print Delta
        # Store relevant variables
        flog.append(fnow) # Current function value

        iteration += 1
        print_out(len_maxiters, display, fnow, current_grad, beta, iteration)

        if success:
            # Test for termination
            if (np.max(np.abs(alpha * d)) < xtol) or (np.abs(fnew - fold) < ftol):
                status = 'converged'
                break
                #return x, flog, function_eval, status

            else:
                # Update variables for new position
                gradnew = f_gradf[1]
                current_grad = np.dot(gradnew, gradnew)
                gradold = gradnew
                fold = fnew
                print 
                print 'Calling local optimisation...'
                local_optimisation(xnew)
                # If the gradient is zero then we are done.
                if current_grad <= gtol:
                    status = 'converged'
                    break
                    # return x, flog, function_eval, status

        # Adjust beta according to comparison ratio.
        if Delta < 0.25:
            beta = min(4.0 * beta, betamax)
        if Delta > 0.75:
            beta = max(0.5 * beta, betamin)

        # Update search direction using Polak-Ribiere formula, or re-start
        # in direction of negative gradient after nparams steps.
        if nsuccess == x.size:
            d = -gradnew
            #beta = 1.  # TODO: betareset!!
            nsuccess = 0
        elif success:
            Gamma = np.dot(gradold - gradnew, gradnew) / (mu)
            if debug:
                print 'Gamma'
                print Gamma
                print 'gradnew'
                print gradnew
                print 
            d = Gamma * d - gradnew
    else:
        # If we get here, then we haven't terminated in the given number of
        # iterations.
        status = "maxiter exceeded"

    if display:
        print_out(len_maxiters, display, fnow, current_grad, beta, iteration)
        print 
    return x, flog, function_eval, status
