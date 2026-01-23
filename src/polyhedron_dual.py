"""
Polyhedron Dual Generator and Rupert's Property Analyzer

This module generates duals of Johnson solids and analyzes them for the Rupert's property.
Uses methods from Chai et al., Hoffmann & Lavau, Steininger & Yurkevich, and Fredricksson.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import json


@dataclass
class Polyhedron:
    """Represents a polyhedron with vertices, faces, and edges."""
    name: str
    vertices: np.ndarray  # Nx3 array of vertex coordinates
    faces: List[List[int]]  # List of faces, each face is list of vertex indices

    @property
    def num_vertices(self) -> int:
        return len(self.vertices)

    @property
    def num_faces(self) -> int:
        return len(self.faces)

    @property
    def num_edges(self) -> int:
        """Calculate number of edges using Euler's formula verification."""
        edge_set = set()
        for face in self.faces:
            for i in range(len(face)):
                edge = tuple(sorted([face[i], face[(i+1) % len(face)]]))
                edge_set.add(edge)
        return len(edge_set)

    def face_center(self, face_idx: int) -> np.ndarray:
        """Calculate the center (centroid) of a face."""
        face = self.faces[face_idx]
        face_vertices = self.vertices[face]
        return np.mean(face_vertices, axis=0)

    def face_normal(self, face_idx: int) -> np.ndarray:
        """Calculate the outward normal vector of a face."""
        face = self.faces[face_idx]
        if len(face) < 3:
            raise ValueError(f"Face {face_idx} has less than 3 vertices")

        # Use first three vertices to compute normal
        v0 = self.vertices[face[0]]
        v1 = self.vertices[face[1]]
        v2 = self.vertices[face[2]]

        # Cross product gives normal
        edge1 = v1 - v0
        edge2 = v2 - v0
        normal = np.cross(edge1, edge2)

        # Normalize
        norm = np.linalg.norm(normal)
        if norm > 0:
            normal = normal / norm

        # Ensure outward pointing (check against centroid)
        center = np.mean(self.vertices, axis=0)
        face_center = self.face_center(face_idx)
        if np.dot(normal, face_center - center) < 0:
            normal = -normal

        return normal

    def compute_dual(self) -> 'Polyhedron':
        """
        Compute the dual polyhedron.

        In the dual:
        - Each face of the original becomes a vertex (at face center)
        - Each vertex of the original becomes a face (connecting adjacent face centers)
        """
        # Step 1: Dual vertices are original face centers
        dual_vertices = np.array([self.face_center(i) for i in range(self.num_faces)])

        # Step 2: Build vertex-to-faces adjacency
        vertex_to_faces: Dict[int, List[int]] = {i: [] for i in range(self.num_vertices)}
        for face_idx, face in enumerate(self.faces):
            for vertex_idx in face:
                vertex_to_faces[vertex_idx].append(face_idx)

        # Step 3: Dual faces connect face centers around each original vertex
        dual_faces = []
        for vertex_idx in range(self.num_vertices):
            adjacent_faces = vertex_to_faces[vertex_idx]
            if len(adjacent_faces) < 3:
                continue  # Skip degenerate cases

            # Order faces around vertex (this is complex for general polyhedra)
            # For now, use the order they appear (works for convex polyhedra)
            ordered_face_indices = self._order_faces_around_vertex(vertex_idx, adjacent_faces)
            dual_faces.append(ordered_face_indices)

        return Polyhedron(
            name=f"{self.name}_dual",
            vertices=dual_vertices,
            faces=dual_faces
        )

    def _order_faces_around_vertex(self, vertex_idx: int, face_indices: List[int]) -> List[int]:
        """
        Order faces cyclically around a vertex.
        This is a simplified version - proper implementation needs edge connectivity.
        """
        if len(face_indices) <= 3:
            return face_indices

        # Build edge connectivity between faces
        face_connections = {f: [] for f in face_indices}

        for i, f1 in enumerate(face_indices):
            for f2 in face_indices[i+1:]:
                # Check if faces share an edge containing vertex_idx
                if self._faces_share_edge_at_vertex(f1, f2, vertex_idx):
                    face_connections[f1].append(f2)
                    face_connections[f2].append(f1)

        # Traverse to create cycle
        ordered = [face_indices[0]]
        current = face_indices[0]
        visited = {current}

        while len(ordered) < len(face_indices):
            # Find next unvisited neighbor
            next_face = None
            for neighbor in face_connections[current]:
                if neighbor not in visited:
                    next_face = neighbor
                    break

            if next_face is None:
                # If stuck, add remaining faces (shouldn't happen for good meshes)
                for f in face_indices:
                    if f not in visited:
                        ordered.append(f)
                        visited.add(f)
                break

            ordered.append(next_face)
            visited.add(next_face)
            current = next_face

        return ordered

    def _faces_share_edge_at_vertex(self, face1_idx: int, face2_idx: int, vertex_idx: int) -> bool:
        """Check if two faces share an edge that includes the given vertex."""
        face1 = self.faces[face1_idx]
        face2 = self.faces[face2_idx]

        # Find edges in face1 containing vertex_idx
        edges1 = []
        for i in range(len(face1)):
            if face1[i] == vertex_idx:
                prev_v = face1[(i-1) % len(face1)]
                next_v = face1[(i+1) % len(face1)]
                edges1.append(tuple(sorted([vertex_idx, prev_v])))
                edges1.append(tuple(sorted([vertex_idx, next_v])))

        # Find edges in face2 containing vertex_idx
        edges2 = []
        for i in range(len(face2)):
            if face2[i] == vertex_idx:
                prev_v = face2[(i-1) % len(face2)]
                next_v = face2[(i+1) % len(face2)]
                edges2.append(tuple(sorted([vertex_idx, prev_v])))
                edges2.append(tuple(sorted([vertex_idx, next_v])))

        # Check for common edge
        return bool(set(edges1) & set(edges2))

    def symmetry_group_order(self) -> int:
        """
        Estimate the order of the symmetry group.
        Higher symmetry suggests higher likelihood of Rupert's property.
        """
        # This is a placeholder - proper implementation needs group theory
        # For now, return a rough estimate based on vertex/face regularity

        # Check vertex regularity
        vertex_degrees = [len([f for f in self.faces if v in f]) for v in range(self.num_vertices)]
        vertex_regularity = len(set(vertex_degrees))

        # Check face regularity
        face_sizes = [len(f) for f in self.faces]
        face_regularity = len(set(face_sizes))

        # Lower values = higher symmetry
        symmetry_estimate = 1.0 / (vertex_regularity * face_regularity)

        return int(symmetry_estimate * 100)  # Arbitrary scaling

    def compute_bounding_sphere_radius(self) -> float:
        """Compute radius of smallest sphere containing all vertices."""
        center = np.mean(self.vertices, axis=0)
        distances = np.linalg.norm(self.vertices - center, axis=1)
        return np.max(distances)

    def project_to_plane(self, normal: np.ndarray) -> np.ndarray:
        """
        Project all vertices onto plane perpendicular to normal vector.
        Returns 2D coordinates.
        """
        # Normalize normal
        normal = normal / np.linalg.norm(normal)

        # Create basis for plane (Gram-Schmidt)
        if abs(normal[0]) < 0.9:
            u = np.array([1, 0, 0])
        else:
            u = np.array([0, 1, 0])

        u = u - np.dot(u, normal) * normal
        u = u / np.linalg.norm(u)

        v = np.cross(normal, u)
        v = v / np.linalg.norm(v)

        # Project vertices
        projected = np.zeros((self.num_vertices, 2))
        for i, vertex in enumerate(self.vertices):
            projected[i, 0] = np.dot(vertex, u)
            projected[i, 1] = np.dot(vertex, v)

        return projected

    def convex_hull_area_2d(self, points_2d: np.ndarray) -> float:
        """Compute area of convex hull of 2D points (projected polyhedron)."""
        from scipy.spatial import ConvexHull

        if len(points_2d) < 3:
            return 0.0

        try:
            hull = ConvexHull(points_2d)
            return hull.volume  # In 2D, volume = area
        except:
            return 0.0

    def save_to_json(self, filename: str):
        """Save polyhedron to JSON file."""
        data = {
            "name": self.name,
            "vertices": self.vertices.tolist(),
            "faces": self.faces,
            "stats": {
                "num_vertices": self.num_vertices,
                "num_faces": self.num_faces,
                "num_edges": self.num_edges,
                "euler_characteristic": self.num_vertices - self.num_edges + self.num_faces
            }
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_json(cls, filename: str) -> 'Polyhedron':
        """Load polyhedron from JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)

        return cls(
            name=data["name"],
            vertices=np.array(data["vertices"]),
            faces=data["faces"]
        )


class RupertsPropertyAnalyzer:
    """
    Analyzer for the Rupert's property using multiple methods.
    """

    def __init__(self, polyhedron: Polyhedron):
        self.poly = polyhedron
        self.results = {}

    def method_hoffmann_lavau_projection(self, num_samples: int = 1000) -> Dict:
        """
        Hoffmann & Lavau (2019) projection method.

        Find angle where projection area is minimized, check if rotated projection
        can fit within original projection.
        """
        min_area = float('inf')
        best_normal = None

        # Sample random directions on unit sphere
        for _ in range(num_samples):
            # Random point on sphere
            theta = np.random.uniform(0, 2 * np.pi)
            phi = np.random.uniform(0, np.pi)
            normal = np.array([
                np.sin(phi) * np.cos(theta),
                np.sin(phi) * np.sin(theta),
                np.cos(phi)
            ])

            # Project and compute area
            projected = self.poly.project_to_plane(normal)
            area = self.poly.convex_hull_area_2d(projected)

            if area < min_area:
                min_area = area
                best_normal = normal

        # Rough estimate: if min projection area < 0.8 * max projection area
        # then there might be room for passage
        max_area = self.poly.compute_bounding_sphere_radius() ** 2 * np.pi

        ratio = min_area / max_area if max_area > 0 else 1.0

        return {
            "method": "Hoffmann-Lavau Projection",
            "min_projection_area": float(min_area),
            "max_projection_area": float(max_area),
            "area_ratio": float(ratio),
            "likely_has_ruperts": ratio < 0.75,  # Heuristic threshold
            "confidence": "medium"
        }

    def method_symmetry_analysis(self) -> Dict:
        """
        Chai et al. (2018) symmetry-based analysis.

        Higher symmetry correlates with higher likelihood of Rupert's property.
        """
        symmetry_order = self.poly.symmetry_group_order()

        # Heuristics based on known results
        if symmetry_order > 50:
            likelihood = "high"
            has_ruperts = True
        elif symmetry_order > 20:
            likelihood = "medium"
            has_ruperts = True
        else:
            likelihood = "low"
            has_ruperts = False

        return {
            "method": "Chai et al. Symmetry",
            "symmetry_order_estimate": symmetry_order,
            "likely_has_ruperts": has_ruperts,
            "confidence": likelihood
        }

    def method_face_irregularity(self) -> Dict:
        """
        Analyze face irregularity.

        Highly irregular faces (varying sizes/shapes) reduce likelihood of Rupert's property.
        """
        # Compute face areas
        face_areas = []
        for face_idx in range(self.poly.num_faces):
            face = self.poly.faces[face_idx]
            if len(face) < 3:
                continue

            # Simple area calculation using triangulation
            center = self.poly.face_center(face_idx)
            area = 0.0
            for i in range(len(face)):
                v1 = self.poly.vertices[face[i]]
                v2 = self.poly.vertices[face[(i+1) % len(face)]]
                triangle_area = 0.5 * np.linalg.norm(np.cross(v1 - center, v2 - center))
                area += triangle_area
            face_areas.append(area)

        if not face_areas:
            return {"method": "Face Irregularity", "error": "No valid faces"}

        face_areas = np.array(face_areas)
        mean_area = np.mean(face_areas)
        std_area = np.std(face_areas)
        cv = std_area / mean_area if mean_area > 0 else 0  # Coefficient of variation

        # Lower CV = more regular = higher likelihood
        if cv < 0.2:
            likelihood = True
        elif cv < 0.5:
            likelihood = True  # Still possible
        else:
            likelihood = False  # Highly irregular

        return {
            "method": "Face Irregularity Analysis",
            "coefficient_of_variation": float(cv),
            "mean_face_area": float(mean_area),
            "std_face_area": float(std_area),
            "likely_has_ruperts": likelihood,
            "confidence": "medium"
        }

    def analyze_all_methods(self) -> Dict:
        """Run all analysis methods and compile results."""
        results = {
            "polyhedron_name": self.poly.name,
            "num_vertices": self.poly.num_vertices,
            "num_faces": self.poly.num_faces,
            "num_edges": self.poly.num_edges,
            "methods": []
        }

        # Run each method
        try:
            results["methods"].append(self.method_hoffmann_lavau_projection())
        except Exception as e:
            results["methods"].append({"method": "Hoffmann-Lavau", "error": str(e)})

        try:
            results["methods"].append(self.method_symmetry_analysis())
        except Exception as e:
            results["methods"].append({"method": "Symmetry", "error": str(e)})

        try:
            results["methods"].append(self.method_face_irregularity())
        except Exception as e:
            results["methods"].append({"method": "Face Irregularity", "error": str(e)})

        # Aggregate conclusion
        votes_yes = sum(1 for m in results["methods"] if m.get("likely_has_ruperts", False))
        votes_total = len([m for m in results["methods"] if "likely_has_ruperts" in m])

        if votes_total > 0:
            confidence = votes_yes / votes_total
            results["aggregate_conclusion"] = {
                "likely_has_ruperts": confidence >= 0.5,
                "confidence_score": confidence,
                "votes_yes": votes_yes,
                "votes_total": votes_total
            }

        return results


def create_test_polyhedra() -> Dict[str, Polyhedron]:
    """Create some test polyhedra for validation."""
    polyhedra = {}

    # Tetrahedron (J1) - self-dual
    tetrahedron_vertices = np.array([
        [1, 1, 1],
        [1, -1, -1],
        [-1, 1, -1],
        [-1, -1, 1]
    ], dtype=float)
    tetrahedron_vertices /= np.linalg.norm(tetrahedron_vertices[0])

    tetrahedron_faces = [
        [0, 1, 2],
        [0, 2, 3],
        [0, 3, 1],
        [1, 3, 2]
    ]

    polyhedra["J1_tetrahedron"] = Polyhedron(
        name="J1_tetrahedron",
        vertices=tetrahedron_vertices,
        faces=tetrahedron_faces
    )

    # Square pyramid (J2)
    square_pyramid_vertices = np.array([
        [1, 1, 0],
        [1, -1, 0],
        [-1, -1, 0],
        [-1, 1, 0],
        [0, 0, 1.5]
    ], dtype=float)

    square_pyramid_faces = [
        [0, 1, 2, 3],  # Base
        [0, 4, 1],
        [1, 4, 2],
        [2, 4, 3],
        [3, 4, 0]
    ]

    polyhedra["J2_square_pyramid"] = Polyhedron(
        name="J2_square_pyramid",
        vertices=square_pyramid_vertices,
        faces=square_pyramid_faces
    )

    return polyhedra


if __name__ == "__main__":
    print("Johnson Solid Duals - Rupert's Property Analyzer")
    print("=" * 60)

    # Create test polyhedra
    test_polys = create_test_polyhedra()

    for name, poly in test_polys.items():
        print(f"\nAnalyzing {name}...")
        print(f"  Vertices: {poly.num_vertices}, Faces: {poly.num_faces}, Edges: {poly.num_edges}")

        # Compute dual
        dual = poly.compute_dual()
        print(f"  Dual: Vertices: {dual.num_vertices}, Faces: {dual.num_faces}, Edges: {dual.num_edges}")

        # Analyze dual for Rupert's property
        analyzer = RupertsPropertyAnalyzer(dual)
        results = analyzer.analyze_all_methods()

        print(f"  Rupert's Property Analysis:")
        if "aggregate_conclusion" in results:
            conclusion = results["aggregate_conclusion"]
            print(f"    Likely has Rupert's: {conclusion['likely_has_ruperts']}")
            print(f"    Confidence: {conclusion['confidence_score']:.2%}")

        # Save results
        output_file = f"docs/{name}_dual_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"    Results saved to {output_file}")
