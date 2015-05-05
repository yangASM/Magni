"""
..
    Copyright (c) 2014-2015, Magni developers.
    All rights reserved.
    See LICENSE.rst for further information.

Module providing AFM image reconstruction and analysis of reconstructed images.

Routine listings
----------------
analyse(x, Phi, Psi)
    Sample an image, reconstruct it, and analyse the reconstructed image.
reconstruct(y, Phi, Psi)
    Reconstruct an image from compressively sensed measurements.

"""

from __future__ import division

import numpy as np

from magni.afm import config as _conf
from magni.cs.reconstruction import iht as _iht
from magni.cs.reconstruction import it as _it
from magni.cs.reconstruction import sl0 as _sl0
from magni.imaging import evaluation as _eval
from magni.imaging import visualisation as _visualisation
from magni.utils.matrices import Matrix as _Matrix
from magni.utils.matrices import MatrixCollection as _MatrixC
from magni.utils.validation import decorate_validation as _decorate_validation
from magni.utils.validation import validate_numeric as _numeric


def analyse(x, Phi, Psi):
    """
    Sample an image, reconstruct it, and analyse the reconstructed image.

    Parameters
    ----------
    x : numpy.ndarray
        The original image vector.
    Phi : magni.utils.matrices.Matrix or numpy.matrix
        The measurement matrix.
    Psi : magni.utils.matrices.Matrix or numpy.matrix
        The dictionary.

    Returns
    -------
    x : numpy.ndarray
        The reconstructed image vector.

    See Also
    --------
    magni.afm.config : Configuration options.
    magni.imaging.evaluation : Image reconstruction quality evaluation.

    Examples
    --------
    Prior to the actual example, data is loaded and a measurement matrix and a
    dictionary are defined. First, the example MI file provided with the
    package is loaded:

    >>> import os, numpy as np, magni
    >>> from magni.afm.reconstruction import analyse
    >>> path = magni.utils.split_path(magni.__path__[0])[0]
    >>> path = path + 'examples' + os.sep + 'example.mi'
    >>> if os.path.isfile(path):
    ...     mi_file = magni.afm.io.read_mi_file(path)
    ...     mi_buffer = mi_file.get_buffer('Topography')[0]
    ...     mi_data = mi_buffer.data
    ...     x = magni.imaging.mat2vec(mi_data)

    Next, a measurement matrix is defined. This matrix is equal to the matrix
    generated by running `np.eye(len(x))[::2, :]` but for speed, the matrix is
    instead defined with fast operations:

    >>> def Phi_A(x):
    ...     y = x[::2]
    ...     return y
    >>> def Phi_T(y):
    ...     x = np.zeros((2 * len(y), 1))
    ...     x[::2] = y
    ...     return x
    >>> if os.path.isfile(path):
    ...     Phi = magni.utils.matrices.Matrix(Phi_A, Phi_T, (),
    ...                                       (int(len(x) / 2), len(x)))

    Next, a dictionary is defined. This dictionary is the DCT basis likewise
    defined with fast operations:

    >>> if os.path.isfile(path):
    ...     Psi = magni.imaging.dictionaries.get_DCT(mi_data.shape)

    Finally, the actual example:

    >>> if os.path.isfile(path):
    ...     print('MSE: {:.2f}, PSNR: {:.2f}'.format(*analyse(x, Phi, Psi)))
    ... else:
    ...     print('MSE: 0.24, PSNR: 6.22')
    MSE: 0.24, PSNR: 6.22

    """

    @_decorate_validation
    def validate_input():
        _numeric('x', ('integer', 'floating', 'complex'), shape=(-1, 1))
        _numeric('Phi', ('integer', 'floating', 'complex'),
                 shape=(-1, x.shape[0]))
        _numeric('Psi', ('integer', 'floating', 'complex'),
                 shape=(x.shape[0], -1))

    validate_input()

    y = Phi.dot(x)
    x_hat = reconstruct(y, Phi, Psi)

    x_scaled = _visualisation.stretch_image(x, 1.0)
    x_hat_scaled = _visualisation.stretch_image(x_hat, 1.0)

    mse = _eval.calculate_mse(x_scaled, x_hat_scaled)
    psnr = _eval.calculate_psnr(x_scaled, x_hat_scaled, 1.0)

    return (mse, psnr)


def reconstruct(y, Phi, Psi):
    """
    Reconstruct an image from compressively sensed measurements.

    Parameters
    ----------
    y : numpy.ndarray
        The measurement vector.
    Phi : magni.utils.matrices.Matrix or numpy.matrix
        The measurement matrix.
    Psi : magni.utils.matrices.Matrix or numpy.matrix
        The dictionary.

    Returns
    -------
    x : numpy.ndarray
        The reconstructed image vector.

    See Also
    --------
    magni.afm.config : Configuration options.
    magni.cs.reconstruction : Compressed sensing reconstruction algorithms.

    Examples
    --------
    Prior to the actual example, data is loaded and a measurement matrix and a
    dictionary are defined. First, the example MI file provided with the
    package is loaded:

    >>> import os, numpy as np, magni
    >>> from magni.afm.reconstruction import reconstruct
    >>> path = magni.utils.split_path(magni.__path__[0])[0]
    >>> path = path + 'examples' + os.sep + 'example.mi'
    >>> if os.path.isfile(path):
    ...     mi_file = magni.afm.io.read_mi_file(path)
    ...     mi_buffer = mi_file.get_buffer('Topography')[0]
    ...     mi_data = mi_buffer.data
    ...     x = magni.imaging.mat2vec(mi_data)

    Next, a measurement matrix is defined. This matrix is equal to the matrix
    generated by running `np.eye(len(x))[::2, :]` but for speed, the matrix is
    instead defined with fast operations:

    >>> def Phi_A(x):
    ...     y = x[::2]
    ...     return y
    >>> def Phi_T(y):
    ...     x = np.zeros((2 * len(y), 1))
    ...     x[::2] = y
    ...     return x
    >>> if os.path.isfile(path):
    ...     Phi = magni.utils.matrices.Matrix(Phi_A, Phi_T, (),
    ...                                       (int(len(x) / 2), len(x)))

    Next, a dictionary is defined. This dictionary is the DCT basis likewise
    defined with fast operations:

    >>> if os.path.isfile(path):
    ...     Psi = magni.imaging.dictionaries.get_DCT(mi_data.shape)

    Finally, the actual example:

    >>> if os.path.isfile(path):
    ...     y = Phi.dot(x)
    ...     print('Maximum absolute pixel error: {:.3f}'
    ...           .format(np.abs(reconstruct(y, Phi, Psi) - x).max()))
    ... else:
    ...     print('Maximum absolute pixel error: 0.960')
    Maximum absolute pixel error: 0.960

    """

    @_decorate_validation
    def validate_input():
        _numeric('y', ('integer', 'floating', 'complex'), shape=(-1, 1))
        _numeric('Phi', ('integer', 'floating', 'complex'),
                 shape=(y.shape[0], -1))
        _numeric('Psi', ('integer', 'floating', 'complex'),
                 shape=(Phi.shape[1], -1))

    validate_input()

    A = _MatrixC((Phi, Psi))
    algorithm = _conf['algorithm']

    if algorithm == 'iht':
        algorithm = _iht.run
    elif algorithm == 'it':
        algorithm = _it.run
    elif algorithm == 'sl0':
        A = A.A
        algorithm = _sl0.run

    alpha = algorithm(y, A)
    x = Psi.dot(alpha)

    return x
