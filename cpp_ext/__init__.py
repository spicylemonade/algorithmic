"""
C++ Extensions for LCI Pipeline (Module 12)

Provides optimised C++ implementations of computationally intensive
operations, loaded via ctypes.

Currently implements:
- generate_lightcurve_direct_cpp: forward brightness integral
"""

import os
import ctypes
import numpy as np

_LIB_PATH = os.path.join(os.path.dirname(__file__), "libbrightness.so")


def _load_lib():
    """Load the shared library."""
    if not os.path.exists(_LIB_PATH):
        raise RuntimeError(
            f"C++ extension not found at {_LIB_PATH}. "
            f"Compile with: g++ -O3 -shared -fPIC -o {_LIB_PATH} "
            f"{os.path.join(os.path.dirname(__file__), 'brightness.cpp')}"
        )
    lib = ctypes.CDLL(_LIB_PATH)

    # Set function signature
    lib.generate_lightcurve_direct.restype = None
    lib.generate_lightcurve_direct.argtypes = [
        ctypes.c_void_p,   # normals
        ctypes.c_void_p,   # areas
        ctypes.c_int64,    # n_faces
        ctypes.c_void_p,   # sun_dirs
        ctypes.c_void_p,   # obs_dirs
        ctypes.c_int64,    # n_epochs
        ctypes.c_double,   # c_lambert
        ctypes.c_void_p,   # out
    ]
    return lib


_lib = _load_lib()


def generate_lightcurve_direct_cpp(mesh, sun_dirs, obs_dirs, c_lambert=0.1):
    """Compute brightness at multiple epochs using C++ extension.

    Drop-in replacement for forward_model.generate_lightcurve_direct.

    Parameters
    ----------
    mesh : TriMesh
        Asteroid shape model (needs normals and areas).
    sun_dirs : np.ndarray, shape (N, 3)
        Sun directions in body frame.
    obs_dirs : np.ndarray, shape (N, 3)
        Observer directions in body frame.
    c_lambert : float
        Lambert weight parameter.

    Returns
    -------
    brightness : np.ndarray, shape (N,)
        Brightness at each epoch.
    """
    normals = np.ascontiguousarray(mesh.normals, dtype=np.float64)
    areas = np.ascontiguousarray(mesh.areas, dtype=np.float64)
    sun_dirs = np.ascontiguousarray(sun_dirs, dtype=np.float64)
    obs_dirs = np.ascontiguousarray(obs_dirs, dtype=np.float64)

    n_faces = normals.shape[0]
    n_epochs = sun_dirs.shape[0]

    out = np.zeros(n_epochs, dtype=np.float64)

    _lib.generate_lightcurve_direct(
        normals.ctypes.data,
        areas.ctypes.data,
        ctypes.c_int64(n_faces),
        sun_dirs.ctypes.data,
        obs_dirs.ctypes.data,
        ctypes.c_int64(n_epochs),
        ctypes.c_double(c_lambert),
        out.ctypes.data,
    )

    return out
