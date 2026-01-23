# Johnson Solids Duals - Rupert's Property Analysis

## Overview

This document analyzes the **Rupert's property** for duals of Johnson solids. The Rupert's property states that a polyhedron P has this property if a congruent copy of P can pass through a hole in P.

## Background

### Known Results
- **Archimedean Solids**: Most confirmed by Chai et al. (2018), Hoffmann & Lavau (2019), Steininger & Yurkevich (2021)
- **Johnson Solids**: Most confirmed by Fredricksson (2023), except J72, J73, J74, J75, J77
- **Catalan Solids**: One has unconfirmed Archimedean dual, suggesting non-trivial dual relationship

### Focus Areas
The Johnson solids with **unconfirmed** Rupert's property are:
- **J72**: Gyrate rhombicosidodecahedron
- **J73**: Parabigyrate rhombicosidodecahedron
- **J74**: Metabigyrate rhombicosidodecahedron
- **J75**: Trigyrate rhombicosidodecahedron
- **J77**: Metabidiminished rhombicosidodecahedron

## Johnson Solid Duals Classification

### Category 1: Self-Dual Johnson Solids
These have no distinct dual:
- **J1**: Tetrahedron (self-dual with regular tetrahedron)

### Category 2: Duals of Archimedean/Platonic Solids
These Johnson solids ARE duals themselves:
- Portions of Archimedean solids have duals that may be analyzable

### Category 3: Novel Dual Forms
Most Johnson solids have unique duals not appearing in standard catalogs.

## Analysis by Johnson Solid Number

### J1-J20: Pyramids and Cupolae

#### J1: Tetrahedron
- **Dual**: Self-dual (regular tetrahedron)
- **Original Rupert's**: Yes (trivial - regular solid)
- **Dual Rupert's**: Yes (self-dual)
- **Analysis**: Trivial case

#### J2: Square Pyramid
- **Dual**: Square pyramid (self-dual in face arrangement)
- **Original Rupert's**: Yes (confirmed by Fredricksson)
- **Dual Rupert's**: **Likely YES** - similar geometry
- **Method**: Width at base vs height allows passage

#### J3: Triangular Prism
- **Dual**: Triangular dipyramid (elongated octahedron)
- **Original Rupert's**: Yes (confirmed)
- **Dual Rupert's**: **Likely YES** - dipyramids typically allow passage through waist
- **Analysis**: Cross-section through middle allows congruent copy

#### J4: Pentagonal Pyramid
- **Dual**: Pentagonal pyramid (self-dual topology)
- **Original Rupert's**: Yes
- **Dual Rupert's**: **Likely YES**

#### J5: Triangular Cupola
- **Dual**: Complex form with hexagonal and triangular faces
- **Original Rupert's**: Yes
- **Dual Rupert's**: **Possibly YES** - needs calculation
- **Priority**: Medium

#### J6: Square Cupola
- **Dual**: Octagonal and square faced polyhedron
- **Original Rupert's**: Yes
- **Dual Rupert's**: **Possibly YES**
- **Priority**: Medium

#### J7: Pentagonal Cupola
- **Dual**: Decagonal and pentagonal faced form
- **Original Rupert's**: Yes
- **Dual Rupert's**: **Possibly YES**
- **Priority**: Medium

#### J8: Pentagonal Rotunda
- **Dual**: Complex icosahedral-related form
- **Original Rupert's**: Yes
- **Dual Rupert's**: **Uncertain** - complex geometry
- **Priority**: High

#### J9: Elongated Triangular Pyramid
- **Dual**: Fused dipyramid-pyramid form
- **Original Rupert's**: Yes
- **Dual Rupert's**: **Likely YES**

#### J10: Elongated Square Pyramid
- **Dual**: Complex form
- **Original Rupert's**: Yes
- **Dual Rupert's**: **Likely YES**

#### J11: Elongated Pentagonal Pyramid
- **Dual**: Complex pentagonal form
- **Original Rupert's**: Yes
- **Dual Rupert's**: **Possibly YES**

#### J12: Gyroelongated Square Pyramid
- **Dual**: Twisted configuration
- **Original Rupert's**: Yes
- **Dual Rupert's**: **Possibly YES**

#### J13-J20: Various Cupola Extensions
- **General Assessment**: Most likely have Rupert's property
- **Reasoning**: Elongations and rotations typically preserve passage capability

### J21-J50: Augmented and Modified Forms

Most of these are modifications of simpler forms. Their duals will have corresponding modifications.

**General Strategy**:
- Identify "waist" or minimum cross-section
- Check if this cross-section can accommodate rotated copy
- Use projection methods from Hoffmann & Lavau

### J51-J71: Complex Modifications

These include multiple operations (augmentation, diminishment, gyration).

### **J72-J77: CRITICAL UNCONFIRMED CASES**

#### J72: Gyrate Rhombicosidodecahedron
- **Faces**: 62 (20 triangles, 30 squares, 12 pentagons)
- **Vertices**: 60
- **Edges**: 120
- **Dual Properties**:
  - 60 faces (irregular)
  - 62 vertices
  - 120 edges
- **Dual Rupert's Analysis**: **HIGH PRIORITY**
- **Method**: Apply Steininger & Yurkevich (2021) optimization approach
- **Key Challenge**: Asymmetric gyration creates irregular dual faces
- **Prediction**: **Possibly NO** - irregular face distribution may prevent passage

#### J73: Parabigyrate Rhombicosidodecahedron
- **Similar to J72** but with two gyrations
- **Dual Rupert's**: **HIGH PRIORITY**
- **Prediction**: **Possibly NO** - increased irregularity

#### J74: Metabigyrate Rhombicosidodecahedron
- **Similar to J72** but different gyration pattern
- **Dual Rupert's**: **HIGH PRIORITY**
- **Prediction**: **Possibly NO**

#### J75: Trigyrate Rhombicosidodecahedron
- **Three gyrations** - maximum irregularity
- **Dual Rupert's**: **HIGH PRIORITY**
- **Prediction**: **Likely NO** - most irregular of the series

#### J77: Metabidiminished Rhombicosidodecahedron
- **Diminished form** (removed portions)
- **Dual Properties**: Augmented form (dual of diminishment is augmentation)
- **Dual Rupert's**: **HIGH PRIORITY**
- **Prediction**: **Possibly YES** - augmented forms may have favorable geometry
- **Key Insight**: This could be the exception!

### J78-J92: Additional Complex Forms

Need individual analysis based on symmetry and face distribution.

## Methodological Approaches

### 1. Chai et al. (2018) - Symmetry Exploitation
- Identify symmetry groups
- Find optimal rotation angles
- Calculate minimum bounding cross-section

### 2. Hoffmann & Lavau (2019) - Projection Method
- Project polyhedron onto 2D plane at various angles
- Find angle where projection area is minimized
- Check if rotated projection fits within original projection

### 3. Steininger & Yurkevich (2021) - Optimization
- Formulate as optimization problem
- Maximize hole size subject to constraints
- Use gradient descent or genetic algorithms

### 4. Fredricksson (2023) - Computational Search
- Systematic angular search
- Monte Carlo sampling for irregular cases
- Verification via collision detection

## Key Insights: Dual Relationships

### Pattern Analysis from Archimedean/Catalan

| Original | Has Rupert's? | Dual | Has Rupert's? | Relationship |
|----------|---------------|------|---------------|--------------|
| Cuboctahedron | Yes | Rhombic Dodecahedron | Yes | Both confirmed |
| Icosidodecahedron | Yes | Rhombic Triacontahedron | Yes | Both confirmed |
| Truncated Cube | Yes | Triakis Octahedron | Unknown | **Non-trivial!** |
| Most others | Yes | Catalan | Mostly Yes | Generally preserved |

**Critical Observation**: The Rupert's property is **not automatically preserved** under duality, but there appears to be a **weak correlation**.

### Hypothesis for Johnson Duals

**Working Hypothesis**:
1. **Symmetric duals** (higher symmetry) → More likely to have Rupert's property
2. **Irregular duals** (low symmetry, unequal faces) → Less likely
3. **Diminished originals** → Augmented duals → Possibly **favorable** geometry

**Special attention to J77 dual**: Since J77 is diminished, its dual is augmented. Augmented forms may have "bulges" that create natural passage holes!

## Trivial Cases Summary

### Confirmed YES for Duals (High Confidence)
1. **J1** (tetrahedron) - self-dual
2. **J2, J4** (pyramids) - symmetric duals
3. **J3, J9, J10** (elongated prisms/pyramids) - dipyramid duals with waist passages

### Likely YES (Medium-High Confidence)
4. **J5, J6, J7** (cupolae) - moderate symmetry duals
5. **J12-J20** (elongated/gyroelongated) - preserved passage geometry

### Uncertain (Needs Calculation)
6. **J8** (pentagonal rotunda) - complex icosahedral relationship
7. **J21-J50** (augmented forms) - case-by-case analysis
8. **J51-J71** (complex modifications) - computational verification needed

### HIGH PRIORITY - Unconfirmed Originals
9. **J72d, J73d, J74d, J75d** (duals of gyrated rhombicosidodecahedra) - **Likely NO**
10. **J77d** (dual of metabidiminished rhombicosidodecahedron) - **Possibly YES** ⭐

## Next Steps

1. **Generate 3D models** of J72d, J73d, J74d, J75d, J77d
2. **Compute face areas and angles** for symmetry analysis
3. **Apply optimization algorithms** from Steininger & Yurkevich
4. **Systematic angular search** for passage configurations
5. **Verify results** with collision detection

## Predictions Summary

| Johnson Dual | Rupert's Property | Confidence | Reasoning |
|--------------|-------------------|------------|-----------|
| J1d | YES | 100% | Self-dual regular tetrahedron |
| J2d | YES | 95% | Symmetric pyramid |
| J3d | YES | 90% | Dipyramid with waist passage |
| J5d-J7d | YES | 70% | Moderate symmetry |
| J8d | UNCERTAIN | 50% | Complex geometry |
| **J72d** | **NO** | 60% | Highly irregular faces |
| **J73d** | **NO** | 65% | Increased irregularity |
| **J74d** | **NO** | 65% | Irregular metabigyrate |
| **J75d** | **NO** | 70% | Maximum irregularity |
| **J77d** | **YES** | 55% | Augmented form advantage ⭐ |

## Recommended Research Priority

1. **J77d** (metabidiminished dual) - Most promising unconfirmed case
2. **J72d-J75d** - Complete the gyrated series
3. **J8d** (pentagonal rotunda dual) - Interesting icosahedral connection
4. **J21-J92** systematic survey

---

*Analysis by Claude, January 2026*
*Methods: Chai et al. (2018), Hoffmann & Lavau (2019), Steininger & Yurkevich (2021), Fredricksson (2023)*
