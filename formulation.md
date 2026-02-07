# Mathematical Formulation for the Forward Scattering Model

This document defines the complete mathematical framework used in the Light Curve Inversion pipeline for computing synthetic brightness from a 3D shape model. All notation and variable definitions are specified below.

References: Kaasalainen & Torppa (2001) \cite{kaasalainen2001shape}, Kaasalainen et al. (2001) \cite{kaasalainen2001complete}, Muinonen & Lumme (2015) \cite{muinonen2015lommel}, Muinonen et al. (2010) \cite{muinonen2010hg}.

---

## 1. Brightness Integral for a Faceted Convex Body

### 1.1 Surface Discretization

The asteroid shape is represented as a convex polyhedron with $N_f$ triangular facets. Each facet $k$ has:
- **Area**: $A_k$ (in squared length units, e.g., km²)
- **Outward unit normal**: $\hat{n}_k$
- **Centroid position**: $\mathbf{r}_k$

### 1.2 Illumination and Viewing Geometry per Facet

At a given epoch, define:
- $\hat{e}_\odot$: unit vector from the asteroid center toward the Sun
- $\hat{e}_\oplus$: unit vector from the asteroid center toward the observer (Earth)

For each facet $k$, compute the cosines of the incidence and emission angles:

$$\mu_{0,k} = \hat{n}_k \cdot \hat{e}_\odot$$

$$\mu_k = \hat{n}_k \cdot \hat{e}_\oplus$$

A facet contributes to the observed brightness only if it is both **illuminated** ($\mu_{0,k} > 0$) and **visible** ($\mu_k > 0$).

### 1.3 Scattering Law: Lambert + Lommel-Seeliger Combination

Following Kaasalainen et al. (2001) \cite{kaasalainen2001complete}, we use a combined scattering law that blends the Lambertian and Lommel-Seeliger models:

$$S(\mu_0, \mu, \alpha) = f(\alpha) \left[ (1 - c_L) \frac{\mu_0}{\mu_0 + \mu} + c_L \, \mu_0 \right]$$

where:
- $\mu_0 \equiv \mu_{0,k}$: cosine of incidence angle
- $\mu \equiv \mu_k$: cosine of emission angle
- $\alpha$: phase angle (Sun-asteroid-observer angle)
- $c_L \in [0, 1]$: Lambert weight parameter. $c_L = 0$ gives pure Lommel-Seeliger; $c_L = 1$ gives pure Lambert.
- $f(\alpha)$: phase function accounting for overall brightness variation with phase angle

The **Lommel-Seeliger** term $\mu_0 / (\mu_0 + \mu)$ models single-scattering in a semi-infinite particulate medium and is appropriate for dark, low-albedo surfaces (C-type asteroids). The **Lambert** term $\mu_0$ models ideal diffuse reflection.

### 1.4 Phase Function

The phase function $f(\alpha)$ is a smooth, monotonically decreasing function. For lightcurve inversion where only relative brightnesses matter (not absolute magnitude), a simple exponential model suffices:

$$f(\alpha) = a_0 \exp(-\alpha / d)$$

where $a_0$ is a normalization constant and $d$ is a characteristic angular scale. Since lightcurve inversion operates on relative magnitudes, $a_0$ cancels out and the phase function primarily affects sparse data spanning different phase angles.

For absolute photometry (sparse data calibration), we use the H-G1-G2 system (Muinonen et al. 2010 \cite{muinonen2010hg}):

$$V(\alpha) = H - 2.5 \log_{10}\left[G_1 \Phi_1(\alpha) + G_2 \Phi_2(\alpha) + (1 - G_1 - G_2) \Phi_3(\alpha)\right]$$

where $H$ is the absolute magnitude, $G_1$ and $G_2$ are the slope parameters, and $\Phi_1, \Phi_2, \Phi_3$ are basis functions.

### 1.5 Total Disk-Integrated Brightness

The total brightness observed at epoch $t$ is the sum over all visible and illuminated facets:

$$L(t) = \sum_{k=1}^{N_f} A_k \, S(\mu_{0,k}(t), \mu_k(t), \alpha(t)) \cdot \mathbb{1}[\mu_{0,k}(t) > 0] \cdot \mathbb{1}[\mu_k(t) > 0]$$

where $\mathbb{1}[\cdot]$ is the indicator function.

The observed magnitude is:

$$m(t) = -2.5 \log_{10} L(t) + C$$

where $C$ is an arbitrary constant for each apparition (since we typically fit relative magnitudes).

---

## 2. Viewing Geometry from Orbital Elements

### 2.1 Coordinate Systems

- **Ecliptic frame**: Standard J2000.0 ecliptic coordinates. The Sun is at the origin.
- **Body frame**: Fixed to the asteroid, with the rotation axis along $\hat{z}_\text{body}$.

### 2.2 Heliocentric Position from Orbital Elements

Given osculating orbital elements $(a, e, i, \Omega, \omega, M_0, t_0)$:

1. Compute mean anomaly at epoch $t$:
   $$M(t) = M_0 + n(t - t_0), \quad n = \sqrt{\frac{GM_\odot}{a^3}}$$

2. Solve Kepler's equation for eccentric anomaly $E$:
   $$M = E - e \sin E$$

3. Compute true anomaly $\nu$:
   $$\tan\frac{\nu}{2} = \sqrt{\frac{1+e}{1-e}} \tan\frac{E}{2}$$

4. Compute heliocentric distance:
   $$r = a(1 - e \cos E)$$

5. Transform to ecliptic Cartesian coordinates using the rotation matrices for $(\Omega, i, \omega)$:
   $$\mathbf{r}_\text{ast} = R_z(-\Omega) \, R_x(-i) \, R_z(-\omega) \begin{pmatrix} r\cos\nu \\ r\sin\nu \\ 0 \end{pmatrix}$$

### 2.3 Observer Position and Direction Vectors

Given the Earth's heliocentric position $\mathbf{r}_\oplus(t)$ (from ephemeris or a simplified Earth orbital model):

- **Sun direction** (from asteroid): $\hat{e}_\odot = -\mathbf{r}_\text{ast} / |\mathbf{r}_\text{ast}|$
- **Observer direction** (from asteroid): $\hat{e}_\oplus = (\mathbf{r}_\oplus - \mathbf{r}_\text{ast}) / |\mathbf{r}_\oplus - \mathbf{r}_\text{ast}|$
- **Phase angle**: $\cos\alpha = \hat{e}_\odot \cdot \hat{e}_\oplus$
- **Solar elongation**: $\cos\epsilon = -\hat{r}_\oplus \cdot (\mathbf{r}_\text{ast} - \mathbf{r}_\oplus) / |\mathbf{r}_\text{ast} - \mathbf{r}_\oplus|$

### 2.4 Light-Time Correction

The observed epoch $t_\text{obs}$ differs from the asteroid epoch $t_\text{ast}$ by the light travel time:

$$t_\text{ast} = t_\text{obs} - \frac{|\mathbf{r}_\oplus(t_\text{obs}) - \mathbf{r}_\text{ast}(t_\text{ast})|}{c}$$

This is solved iteratively (1-2 iterations suffice for typical accuracies).

### 2.5 Aspect Angle

The aspect angle $\theta_\text{asp}$ is the angle between the asteroid's spin axis and the observer direction:

$$\cos\theta_\text{asp} = \hat{z}_\text{spin} \cdot \hat{e}_\oplus$$

where $\hat{z}_\text{spin}$ is the spin axis unit vector in ecliptic coordinates, computed from the pole ecliptic longitude $\lambda_p$ and latitude $\beta_p$:

$$\hat{z}_\text{spin} = (\cos\beta_p \cos\lambda_p, \, \cos\beta_p \sin\lambda_p, \, \sin\beta_p)$$

---

## 3. Convex Shape Representation

### 3.1 Gaussian Surface Area Density (Spherical Harmonics)

Following Kaasalainen & Torppa (2001) \cite{kaasalainen2001shape}, a convex shape can be parameterized by the **Gaussian surface area density** $G(\hat{n})$, which gives the area per unit solid angle on the unit sphere as a function of outward normal direction $\hat{n}$.

Expand in real spherical harmonics:

$$G(\theta, \phi) = \exp\left[\sum_{l=0}^{l_\max} \sum_{m=-l}^{l} c_{lm} Y_l^m(\theta, \phi)\right]$$

where:
- $Y_l^m(\theta, \phi)$: real spherical harmonics
- $c_{lm}$: shape coefficients (free parameters for optimization)
- $l_\max$: maximum harmonic degree (typically 6-8 for convex inversion)
- The exponential ensures $G > 0$ (positive area)

The total number of shape parameters is $(l_\max + 1)^2$.

### 3.2 From Gaussian Image to Faceted Mesh

Given $G(\hat{n})$, the convex shape is reconstructed via the **Minkowski problem**: find the convex body whose Gaussian image matches $G$.

In practice, the shape is discretized on a geodesic sphere with $N_f$ facets. Each facet $k$ has a fixed normal direction $\hat{n}_k$ and a variable area:

$$A_k = G(\hat{n}_k) \, \Delta\Omega_k$$

where $\Delta\Omega_k$ is the solid angle subtended by facet $k$ on the unit sphere.

### 3.3 Alternative: Direct Facet Area Parameterization

Instead of spherical harmonics, one can directly optimize the facet areas $\{A_k\}$ subject to:
- $A_k \geq 0$ for all $k$ (non-negativity, ensured by log-parameterization: $A_k = \exp(a_k)$)
- Regularization: $\lambda_\text{reg} \sum_k (A_k - \bar{A})^2$ penalizes non-smooth shapes

---

## 4. Rotation and Body-Frame Transformation

### 4.1 Spin State Parameters

The spin state is defined by:
- **Pole direction**: ecliptic longitude $\lambda_p$ and latitude $\beta_p$ (degrees)
- **Sidereal rotation period**: $P$ (hours)
- **Reference epoch**: $t_0$ (Julian Date) — the epoch at which the body-frame is aligned with the ecliptic frame by a defined convention

### 4.2 Rotation Matrix

At epoch $t$, the rotational phase is:

$$\phi(t) = \phi_0 + \frac{2\pi}{P}(t - t_0)$$

The transformation from ecliptic to body frame involves three rotations:

$$R_\text{ecl \to body}(t) = R_z(\phi(t)) \, R_y(90° - \beta_p) \, R_z(-\lambda_p)$$

The Sun and observer directions in the body frame are:

$$\hat{e}_\odot^\text{body}(t) = R_\text{ecl \to body}(t) \, \hat{e}_\odot^\text{ecl}(t)$$

$$\hat{e}_\oplus^\text{body}(t) = R_\text{ecl \to body}(t) \, \hat{e}_\oplus^\text{ecl}(t)$$

---

## 5. Synthetic Lightcurve Generation

### 5.1 Full Algorithm

Given a shape model (facets with normals $\hat{n}_k$ and areas $A_k$), spin state $(\lambda_p, \beta_p, P, t_0)$, orbital elements, and a set of observation epochs $\{t_j\}_{j=1}^{N_\text{obs}}$:

**For each epoch $t_j$:**
1. Compute heliocentric and geocentric positions (Section 2.2-2.3)
2. Apply light-time correction (Section 2.4)
3. Compute Sun and observer direction vectors in ecliptic frame
4. Transform to body frame using rotation matrix (Section 4.2)
5. For each facet $k$, compute $\mu_{0,k} = \hat{n}_k \cdot \hat{e}_\odot^\text{body}$ and $\mu_k = \hat{n}_k \cdot \hat{e}_\oplus^\text{body}$
6. Sum contributions from visible+illuminated facets:
   $$L(t_j) = \sum_{k: \mu_{0,k}>0, \mu_k>0} A_k \, S(\mu_{0,k}, \mu_k, \alpha_j)$$
7. Convert to magnitude: $m(t_j) = -2.5 \log_{10} L(t_j) + C_j$

### 5.2 Chi-Squared Objective

The inversion minimizes:

$$\chi^2 = \sum_{i=1}^{N_\text{lc}} \sum_{j=1}^{N_i} w_{ij} \left[\frac{L_\text{obs}(t_{ij})}{L_\text{mod}(t_{ij})} - 1\right]^2$$

where:
- $N_\text{lc}$: number of lightcurves
- $N_i$: number of data points in lightcurve $i$
- $w_{ij}$: weight (inverse variance) for data point $j$ of lightcurve $i$
- $L_\text{obs}$: observed relative brightness
- $L_\text{mod}$: modeled relative brightness

For each lightcurve, a separate normalization constant is fit to remove the arbitrary offset.

### 5.3 Sparse Data Integration

For sparse data points at diverse geometries, the chi-squared has an additional term (Durech et al. 2009 \cite{durech2009sparse}):

$$\chi^2_\text{sparse} = \lambda_s \sum_{j=1}^{N_s} w_j \left[\frac{L_\text{obs}^\text{sparse}(t_j)}{L_\text{mod}^\text{sparse}(t_j)} - 1\right]^2$$

where $\lambda_s$ is a relative weight that balances dense and sparse contributions. The sparse brightness must be calibrated to absolute values using the H-G1-G2 phase curve model (Section 1.4).

---

## 6. Variable Definitions Summary

| Symbol | Definition | Units |
|---|---|---|
| $N_f$ | Number of triangular facets | — |
| $A_k$ | Area of facet $k$ | km² |
| $\hat{n}_k$ | Outward unit normal of facet $k$ | — |
| $\hat{e}_\odot$ | Unit vector toward Sun from asteroid | — |
| $\hat{e}_\oplus$ | Unit vector toward observer from asteroid | — |
| $\mu_0$ | Cosine of incidence angle | — |
| $\mu$ | Cosine of emission angle | — |
| $\alpha$ | Phase angle (Sun-asteroid-observer) | radians |
| $c_L$ | Lambert weight in scattering law | — |
| $f(\alpha)$ | Phase function | — |
| $H$ | Absolute magnitude | mag |
| $G_1, G_2$ | Phase curve slope parameters | — |
| $a, e, i, \Omega, \omega, M_0$ | Orbital elements | AU, —, deg, deg, deg, deg |
| $\lambda_p, \beta_p$ | Pole ecliptic longitude and latitude | degrees |
| $P$ | Sidereal rotation period | hours |
| $t_0$ | Reference epoch | JD |
| $c_{lm}$ | Spherical harmonics shape coefficients | — |
| $l_\max$ | Maximum spherical harmonics degree | — |
| $\chi^2$ | Chi-squared residual | — |
| $\lambda_s$ | Sparse data relative weight | — |
| $\lambda_\text{reg}$ | Regularization weight | — |
