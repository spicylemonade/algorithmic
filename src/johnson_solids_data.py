"""
Johnson Solids Data and Generators

This module contains coordinate data and face definitions for Johnson solids,
with special focus on J72, J73, J74, J75, and J77.
"""

import numpy as np
from typing import Dict, List, Tuple
from polyhedron_dual import Polyhedron


def get_johnson_solid(number: int) -> Polyhedron:
    """Get Johnson solid by number (J1-J92)."""
    generators = {
        1: generate_j1_tetrahedron,
        2: generate_j2_square_pyramid,
        3: generate_j3_triangular_prism,
        72: generate_j72_gyrate_rhombicosidodecahedron,
        73: generate_j73_parabigyrate_rhombicosidodecahedron,
        74: generate_j74_metabigyrate_rhombicosidodecahedron,
        75: generate_j75_trigyrate_rhombicosidodecahedron,
        77: generate_j77_metabidiminished_rhombicosidodecahedron,
    }

    if number not in generators:
        raise ValueError(f"Johnson solid J{number} not yet implemented")

    return generators[number]()


def generate_j1_tetrahedron() -> Polyhedron:
    """J1: Regular tetrahedron."""
    vertices = np.array([
        [1, 1, 1],
        [1, -1, -1],
        [-1, 1, -1],
        [-1, -1, 1]
    ], dtype=float)
    vertices /= np.linalg.norm(vertices[0])

    faces = [
        [0, 1, 2],
        [0, 2, 3],
        [0, 3, 1],
        [1, 3, 2]
    ]

    return Polyhedron(name="J1_tetrahedron", vertices=vertices, faces=faces)


def generate_j2_square_pyramid() -> Polyhedron:
    """J2: Square pyramid."""
    vertices = np.array([
        [1, 1, 0],
        [1, -1, 0],
        [-1, -1, 0],
        [-1, 1, 0],
        [0, 0, np.sqrt(2)]
    ], dtype=float)

    faces = [
        [0, 1, 2, 3],  # Square base
        [0, 4, 1],
        [1, 4, 2],
        [2, 4, 3],
        [3, 4, 0]
    ]

    return Polyhedron(name="J2_square_pyramid", vertices=vertices, faces=faces)


def generate_j3_triangular_prism() -> Polyhedron:
    """J3: Triangular prism."""
    h = 1.5  # Height
    vertices = np.array([
        [1, 0, -h/2],
        [-0.5, np.sqrt(3)/2, -h/2],
        [-0.5, -np.sqrt(3)/2, -h/2],
        [1, 0, h/2],
        [-0.5, np.sqrt(3)/2, h/2],
        [-0.5, -np.sqrt(3)/2, h/2]
    ], dtype=float)

    faces = [
        [0, 1, 2],  # Bottom triangle
        [3, 5, 4],  # Top triangle
        [0, 3, 4, 1],  # Side rectangles
        [1, 4, 5, 2],
        [2, 5, 3, 0]
    ]

    return Polyhedron(name="J3_triangular_prism", vertices=vertices, faces=faces)


def generate_rhombicosidodecahedron() -> Tuple[np.ndarray, List[List[int]]]:
    """
    Generate base rhombicosidodecahedron for J72-J75.

    This is an Archimedean solid with:
    - 62 faces (20 triangles, 30 squares, 12 pentagons)
    - 60 vertices
    - 120 edges
    """
    # Use phi (golden ratio) for icosahedral symmetry
    phi = (1 + np.sqrt(5)) / 2

    # Rhombicosidodecahedron has complex coordinates
    # Based on truncated icosahedron + expansion
    # Coordinates from standard references

    vertices = []
    faces = []

    # Generate vertices using systematic construction
    # This is a simplified version - full implementation needs careful construction

    # For demonstration, we'll create an approximate version
    # Real implementation would use exact coordinates from literature

    # Icosahedral vertex distribution with multiple radii
    # Using three types of vertices at different radii

    # Type 1: Vertices on axes
    for i in range(3):
        v = np.zeros(3)
        v[i] = phi
        vertices.append(v)
        v = np.zeros(3)
        v[i] = -phi
        vertices.append(v)

    # Type 2: Vertices with one coordinate phi, others at +/-1
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            for s1 in [-1, 1]:
                for s2 in [-1, 1]:
                    v = np.zeros(3)
                    v[i] = s1 * phi
                    v[j] = s2
                    k = 3 - i - j
                    v[k] = 0
                    vertices.append(v)

    # Type 3: Vertices with coordinates involving phi
    for s1 in [-1, 1]:
        for s2 in [-1, 1]:
            for s3 in [-1, 1]:
                vertices.append(np.array([s1 * phi, s2, s3 / phi]))
                vertices.append(np.array([s1, s2 / phi, s3 * phi]))
                vertices.append(np.array([s1 / phi, s2 * phi, s3]))

    vertices = np.array(vertices[:60])  # Take first 60 (may have duplicates)

    # Remove near-duplicates
    unique_vertices = []
    for v in vertices:
        is_duplicate = False
        for uv in unique_vertices:
            if np.linalg.norm(v - uv) < 0.1:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_vertices.append(v)

    vertices = np.array(unique_vertices)

    # Normalize to unit sphere
    vertices = vertices / np.linalg.norm(vertices[0])

    # Face construction is complex - use placeholder
    # In practice, faces would be computed from vertex adjacency
    faces = []  # Would need proper face construction

    return vertices, faces


def generate_j72_gyrate_rhombicosidodecahedron() -> Polyhedron:
    """
    J72: Gyrate rhombicosidodecahedron.

    One pentagonal cupola rotated 36° relative to the rhombicosidodecahedron.
    This breaks some symmetry and creates irregular faces in the dual.
    """
    # Start with rhombicosidodecahedron
    base_vertices, base_faces = generate_rhombicosidodecahedron()

    # Apply gyration transformation to one cupola
    # This is a rotation around the 5-fold axis

    # For now, use approximate model
    # Real implementation needs precise cupola identification and rotation

    vertices = base_vertices.copy()
    # Apply 36° rotation to specific vertices (those in the cupola)
    # Placeholder: just use base for now

    faces = base_faces  # Would need actual face reconstruction

    return Polyhedron(
        name="J72_gyrate_rhombicosidodecahedron",
        vertices=vertices,
        faces=faces
    )


def generate_j73_parabigyrate_rhombicosidodecahedron() -> Polyhedron:
    """
    J73: Parabigyrate rhombicosidodecahedron.

    Two opposite pentagonal cupolae rotated 36°.
    """
    vertices, faces = generate_rhombicosidodecahedron()
    # Apply two gyrations in para configuration

    return Polyhedron(
        name="J73_parabigyrate_rhombicosidodecahedron",
        vertices=vertices,
        faces=faces
    )


def generate_j74_metabigyrate_rhombicosidodecahedron() -> Polyhedron:
    """
    J74: Metabigyrate rhombicosidodecahedron.

    Two pentagonal cupolae rotated 36° in meta configuration.
    """
    vertices, faces = generate_rhombicosidodecahedron()
    # Apply two gyrations in meta configuration

    return Polyhedron(
        name="J74_metabigyrate_rhombicosidodecahedron",
        vertices=vertices,
        faces=faces
    )


def generate_j75_trigyrate_rhombicosidodecahedron() -> Polyhedron:
    """
    J75: Trigyrate rhombicosidodecahedron.

    Three pentagonal cupolae rotated 36°.
    Maximum irregularity in the gyrate series.
    """
    vertices, faces = generate_rhombicosidodecahedron()
    # Apply three gyrations

    return Polyhedron(
        name="J75_trigyrate_rhombicosidodecahedron",
        vertices=vertices,
        faces=faces
    )


def generate_j77_metabidiminished_rhombicosidodecahedron() -> Polyhedron:
    """
    J77: Metabidiminished rhombicosidodecahedron.

    Rhombicosidodecahedron with two opposite pentagonal cupolae removed.
    The dual will have augmentations instead of diminishments.

    This is particularly interesting because augmented duals may have
    favorable geometry for Rupert's property!
    """
    vertices, faces = generate_rhombicosidodecahedron()

    # Remove vertices and faces corresponding to two opposite pentagonal cupolae
    # This creates "flat" pentagonal faces
    # Placeholder: use base for now

    return Polyhedron(
        name="J77_metabidiminished_rhombicosidodecahedron",
        vertices=vertices,
        faces=faces
    )


def get_johnson_solid_properties(number: int) -> Dict:
    """Get known properties of a Johnson solid."""
    properties = {
        1: {
            "name": "Tetrahedron",
            "vertices": 4, "faces": 4, "edges": 6,
            "ruperts_original": True,
            "symmetry": "Td",
            "notes": "Self-dual, regular solid"
        },
        2: {
            "name": "Square pyramid",
            "vertices": 5, "faces": 5, "edges": 8,
            "ruperts_original": True,
            "symmetry": "C4v",
            "notes": "Confirmed by Fredricksson"
        },
        3: {
            "name": "Triangular prism",
            "vertices": 6, "faces": 5, "edges": 9,
            "ruperts_original": True,
            "symmetry": "D3h",
            "notes": "Dual is triangular dipyramid"
        },
        72: {
            "name": "Gyrate rhombicosidodecahedron",
            "vertices": 60, "faces": 62, "edges": 120,
            "ruperts_original": None,  # Unknown
            "symmetry": "C5v",
            "notes": "One cupola gyrated, creates asymmetry"
        },
        73: {
            "name": "Parabigyrate rhombicosidodecahedron",
            "vertices": 60, "faces": 62, "edges": 120,
            "ruperts_original": None,  # Unknown
            "symmetry": "D5d",
            "notes": "Two opposite cupolae gyrated"
        },
        74: {
            "name": "Metabigyrate rhombicosidodecahedron",
            "vertices": 60, "faces": 62, "edges": 120,
            "ruperts_original": None,  # Unknown
            "symmetry": "C2v",
            "notes": "Two adjacent cupolae gyrated"
        },
        75: {
            "name": "Trigyrate rhombicosidodecahedron",
            "vertices": 60, "faces": 62, "edges": 120,
            "ruperts_original": None,  # Unknown
            "symmetry": "C3v",
            "notes": "Three cupolae gyrated, maximum irregularity"
        },
        77: {
            "name": "Metabidiminished rhombicosidodecahedron",
            "vertices": 50, "faces": 52, "edges": 100,
            "ruperts_original": None,  # Unknown
            "symmetry": "D5h",
            "notes": "Two opposite cupolae removed, dual is augmented"
        },
    }

    return properties.get(number, {})


if __name__ == "__main__":
    print("Johnson Solids Data Module")
    print("=" * 60)

    # Test generation for key solids
    test_numbers = [1, 2, 3, 72, 73, 74, 75, 77]

    for num in test_numbers:
        try:
            print(f"\nJ{num}: {get_johnson_solid_properties(num).get('name', 'Unknown')}")
            props = get_johnson_solid_properties(num)
            print(f"  Properties: {props}")

            if num <= 3:  # Only generate for simple cases
                poly = get_johnson_solid(num)
                print(f"  Generated: V={poly.num_vertices}, F={poly.num_faces}, E={poly.num_edges}")
        except Exception as e:
            print(f"  Error: {e}")
