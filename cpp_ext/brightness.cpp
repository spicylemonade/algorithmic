/**
 * C++ extension for the forward brightness integral.
 *
 * Computes disk-integrated brightness of a faceted mesh at multiple epochs
 * using Lambert + Lommel-Seeliger scattering law.
 *
 * Compiled as a shared library and called via ctypes from Python.
 *
 * Build:
 *   g++ -O3 -shared -fPIC -o libbrightness.so brightness.cpp
 */

#include <cmath>
#include <cstdint>

extern "C" {

/**
 * Compute brightness at multiple epochs for a faceted mesh.
 *
 * Parameters:
 *   normals:   (n_faces, 3) face unit normals (row-major)
 *   areas:     (n_faces,) face areas
 *   n_faces:   number of faces
 *   sun_dirs:  (n_epochs, 3) sun directions in body frame (row-major)
 *   obs_dirs:  (n_epochs, 3) observer directions in body frame (row-major)
 *   n_epochs:  number of epochs
 *   c_lambert: Lambert weight parameter
 *   out:       (n_epochs,) output brightness array
 */
void generate_lightcurve_direct(
    const double* normals,  // (n_faces, 3)
    const double* areas,    // (n_faces,)
    int64_t n_faces,
    const double* sun_dirs, // (n_epochs, 3)
    const double* obs_dirs, // (n_epochs, 3)
    int64_t n_epochs,
    double c_lambert,
    double* out             // (n_epochs,)
) {
    const double c_ls = 1.0 - c_lambert;
    const double eps = 1e-30;

    for (int64_t j = 0; j < n_epochs; j++) {
        double sx = sun_dirs[j * 3 + 0];
        double sy = sun_dirs[j * 3 + 1];
        double sz = sun_dirs[j * 3 + 2];
        double ox = obs_dirs[j * 3 + 0];
        double oy = obs_dirs[j * 3 + 1];
        double oz = obs_dirs[j * 3 + 2];

        double brightness = 0.0;

        for (int64_t k = 0; k < n_faces; k++) {
            double nx = normals[k * 3 + 0];
            double ny = normals[k * 3 + 1];
            double nz = normals[k * 3 + 2];

            double mu0 = nx * sx + ny * sy + nz * sz;  // cos incidence
            double mu  = nx * ox + ny * oy + nz * oz;   // cos emission

            if (mu0 > 0.0 && mu > 0.0) {
                // Lommel-Seeliger: mu0 / (mu0 + mu)
                double ls = mu0 / (mu0 + mu + eps);
                // Lambert: mu0
                double S = c_ls * ls + c_lambert * mu0;
                brightness += areas[k] * S;
            }
        }

        out[j] = brightness;
    }
}

} // extern "C"
