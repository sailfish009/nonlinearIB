from __future__ import print_function

import numpy as np
import scipy
import scipy.optimize

import keras.backend as K
import keras
from collections import namedtuple


class ParameterTrainer(keras.callbacks.Callback):
    def __init__(self, loss, parameter, trn, minibatchsize, 
                 first_epoch=0, 
                 init_value=None, 
                 bounds=None, 
                 *kargs, **kwargs):
        """
        This callback selects the value of parameter (a Keras variable, 
        typically a parameter of some layer) that minimizes loss (another Keras
        variable).  It uses scipy.optimize.minimize to do so, and feeds 
        in stochastically sampled minibatches of traininig data
        
        Parameters
        ----------
        loss : Keras variable
            The loss to minimize.
        parameter : Keras variable
            The variable to minimize over
        trn : np.array
            Training data to use while minimizing
        minibatchsize : int
            Number of training data to sample during each gradient step
        first_epoch : int, optional
            First epoch on which to begin training parameter
        init_value : int, optional
            Initial value of parameter to feed into optimizer.  None to use
            current value.
        bounds : list, optional
            Bounds to provide to optimizer.
        """
        
        super(ParameterTrainer, self).__init__(*kargs, **kwargs)
        self.loss = loss
        self.parameter = parameter
        self.trn = trn
        self.minibatchsize = minibatchsize
        self.first_epoch = first_epoch
        self.init_value = init_value
        self.bounds = bounds

    def on_train_begin(self, logs={}):
        """Initialize objective and jacobian functions.
        """
        
        inputs = self.model.inputs + self.model.targets + self.model.sample_weights + [ K.learning_phase(),]
        f_obj = K.function(inputs, [self.loss,])
        #f_jac = K.function(inputs, [K.gradients(self.loss, self.parameter),])
        
        # def getixs(x):
        #     """Sample random indices.  We store the sampled indices so that they are
        #     available from both the objective and jacobian functions.
        #     self.random_samples should be reinitalized as a blank dictionary before
        #     every optimization run.
        #     """
        #     k = x.flat[0]
        #     if k not in self.random_samples:
        #         self.random_samples[k] = np.random.choice(len(self.trn.X), self.minibatchsize)
        #     return self.random_samples[k]
        
        ixs = np.random.choice(len(self.trn.X), self.minibatchsize)
        # def getixs(x):
        #     return ixs
        
        # def optfunc(x):
        #     oldval = K.get_value(self.parameter)
        #     K.set_value(self.parameter, x.flat[0])
        #     # TODO print("Objective at", x, "=", r, " jacbian=", r2)
        #     r  = f_obj([self.trn.X[ixs], self.trn.Y[ixs], np.ones(self.minibatchsize), 1])[0]
        #     r2 = f_jac([self.trn.X[ixs], self.trn.Y[ixs], np.ones(self.minibatchsize), 1])
        #     r2 = np.atleast_2d(np.array(r2[0]))[0]
        #     K.set_value(self.parameter, oldval)
        #     return [r, r2]
        def optfunc(x):
            oldval = K.get_value(self.parameter)
            K.set_value(self.parameter, x)
            # TODO print("Objective at", x, "=", r, " jacbian=", r2)
            r  = f_obj([self.trn.X[ixs], self.trn.Y[ixs], np.ones(self.minibatchsize), 1])[0]
            K.set_value(self.parameter, oldval)
            return r
        
        self.optfunc = optfunc
        
    def do_optimization(self):
        if self.init_value is None:
            init_value = K.get_value(self.parameter).flat[0]
        else:
            init_value = self.init_value
        #r = scipy.optimize.minimize(self.optfunc, init_value, jac=True, bounds=self.bounds, method='SLSQP')
        #best_val = r.x.flat[0]
        r = scipy.optimize.minimize_scalar(self.optfunc, method='brent')
        best_val = r.x
        K.set_value(self.parameter, best_val)

    def on_epoch_begin(self, epoch, logs={}):
        if epoch >= self.first_epoch:
            self.do_optimization()
        
        
    def on_train_end(self, logs={}):
        self.do_optimization()
        

# class AddToLoss(keras.callbacks.Callback):
#     def __init__(self, layer, loss, on_epoch, *kargs, **kwargs):
#         super(AddToLoss, self).__init__(*kargs, **kwargs)
#         self.on_epoch = on_epoch
#         self.loss = loss
#         self.layer = layer
#     def on_epoch_begin(self, epoch, logs={}):
#         if epoch == self.on_epoch:
#             self.layer.add_loss([self.loss,])

        

def np_entropy(p):
    """Compute Shannon entropy of a non-Keras variable.
    """
    cp = np.log(p)
    cp[np.isclose(p,0.)]=0.
    return -p.dot(cp)


# def logsumexp(mx, axis=0):
#     """Use Keras to compute logsumexp.
#     """
#     cmax = K.max(mx, axis=axis)
#     cmax2 = K.expand_dims(cmax, 1)
#     mx2 = mx - cmax2
#     return cmax + K.log(K.sum(K.exp(mx2), axis=1))


def dist_mx(X):
    """Keras code to compute the pairwise distance matrix for a set of
    vectors specifie by the matrix X.
    """
    x2 = K.expand_dims(K.sum(K.square(X), axis=1), 1)
    dists = x2 + K.transpose(x2) - 2*K.dot(X, K.transpose(X))
    return dists


def get_mnist(trainN=None, testN=None):
    """Initialize MNIST dataset.
    """
    
    nb_classes = 10
    (X_train, y_train), (X_test, y_test) = keras.datasets.mnist.load_data()
    X_train = np.reshape(X_train, [X_train.shape[0], -1]).astype('float32') / 255.
    X_test  = np.reshape(X_test , [X_test.shape[0] , -1]).astype('float32') / 255.
    X_train = X_train * 2.0 - 1.0
    X_test  = X_test  * 2.0 - 1.0

    if trainN is not None:
        X_train = X_train[0:trainN]
        y_train = y_train[0:trainN]

    if testN is not None:
        X_test = X_test[0:testN]
        y_test = y_test[0:testN]

    Y_train = keras.utils.np_utils.to_categorical(y_train, nb_classes)
    Y_test  = keras.utils.np_utils.to_categorical(y_test, nb_classes)

    Dataset = namedtuple('Dataset',['X','Y','y','nb_classes'])
    trn = Dataset(X_train, Y_train, y_train, nb_classes)
    tst = Dataset(X_test , Y_test, y_test, nb_classes)

    del X_train, X_test, Y_train, Y_test, y_train, y_test
    
    return trn, tst


# Backend specific code

if K._BACKEND == 'tensorflow':
    import tensorflow as tf
    def K_n_choose_k(n, k, seed=None):
        """Keras code for drawing k samples, without replacement, from 1..n.
        """
        if seed is None:
            seed = np.random.randint(10e6)
        x = tf.range(0, limit=n, dtype='int32')
        x = tf.random_shuffle(x, seed=seed)
        x = x[0:k]
        return x

    def tensor_eye(size):
        """Keras code for generating an identity matrix.
        """
        return tf.eye(size)

    def tensor_constant(x):
        """Convert a numpy array into a Keras constant.
        """
        return tf.constant(x) 

    
else:
    # See descriptions above.
    
    import theano.tensor as T
    def K_n_choose_k(n, k, seed=None):
        from theano.tensor.shared_randomstreams import RandomStreams
        if seed is None:
            seed = np.random.randint(1, 10e6)
        rng = RandomStreams(seed=seed)
        r = rng.choice(size=(k,), a=n, replace=False, dtype='int32')
        return r

    def tensor_eye(size):
        return T.eye(size)

    def tensor_constant(x):
        return K.variable(x)


