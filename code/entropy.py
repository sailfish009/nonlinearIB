# Utility functions for computing entropy values

import numpy as np
import tensorflow as tf
import scipy

def entropy(ps):
    return -np.sum([p*np.log(p) for p in ps if not np.isclose(p,0)])

def gaussian_entropy(d, var):
    # Entropy of a Gaussian distribution with 'd' dimensions and log variance 'log_var'
    h = 0.5 * d * (tf.cast(tf.log(2.0 * np.pi * np.exp(1)), tf.float32) + tf.log(var))
    return h

def gaussian_entropy_np(d, var):
    # Entropy of a Gaussian distribution with 'd' dimensions and log variance 'log_var'
    h = 0.5 * d * (np.log(2.0 * np.pi * np.exp(1)) + np.log(var))
    return h


def GMM_entropy(dist, var, d, bound='upper'):
    # computes bounds for the entropy of a homoscedastic Gaussian mixture model [Kolchinsky, 2017]
    # dist: a matrix of pairwise distances
    # log_var: the log-variance of the mixture components
    # d: number of dimensions
    # n: number of mixture components
    n = tf.cast(tf.shape(dist)[0], tf.float32)
    # var = tf.exp(log_var) + 1e-10

    if bound is 'upper':
        dist_norm = - dist / (2.0 * var)  # uses the KL distance
    elif bound is 'lower':
        dist_norm = - dist / (8.0 * var)  # uses the Bhattacharyya distance
    else:
        print('Error: invalid bound argument')
        return 0

    const = 0.5 * d * tf.log(2.0 * np.pi * np.exp(1.0) * var) + tf.log(n)
    h = const - tf.reduce_mean(tf.reduce_logsumexp(dist_norm, 1))
    return h


def pairwise_distance(x):
    # returns a matrix where each element is the squared distance between each pair of rows in x
    orig_dtype = x.dtype
    
    # these calculations are numerically sensitive, so let's convert to float64
    x = tf.cast(x, tf.float64)
    
    xx = tf.reduce_sum(tf.square(x), 1, keepdims=True)
    dist = xx - 2.0 * tf.matmul(x, tf.transpose(x)) + tf.transpose(xx)
    
    dist = tf.cast(dist, orig_dtype)
    
    dist = tf.nn.relu(dist)  # turn negative numbers into 0 (we only get negatives due to numerical errors)

    return dist

def pairwise_distance2_np(x, x2):
    # these calculations are numerically sensitive, so let's convert to float64
    origtype = x.dtype
    
    x = x.astype('float64')
    x2 = x2.astype('float64')
    
    # returns a matrix where each element is the squared distance between each pair of rows in x and x2
    xx = np.sum(x**2, axis=1)[:,None]
    x2x = np.sum(x2**2, axis=1)[:,None]
    dist = xx + x2x.T - 2.0 * x.dot(x2.T)
    
    dist = dist.astype(origtype)
    
    dist[dist<0] = 0.0  # turn negative numbers into 0 (we only get negatives due to numerical errors)
    
    return dist
