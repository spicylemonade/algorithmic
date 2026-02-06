"""Data loader interfaces for ALCDEF/PDS/Gaia/ZTF/Pan-STARRS/MPC."""


def load_dense_lightcurves(target_id: str):
    return []


def load_sparse_photometry(target_id: str):
    return []


def load_orbital_elements(target_id: str):
    return {}
