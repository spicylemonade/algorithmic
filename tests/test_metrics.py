import unittest
from src.lci.metrics import hausdorff_distance, volumetric_iou, rms_residual, spin_vector_angular_error_deg


class TestMetrics(unittest.TestCase):
    def test_hausdorff(self):
        a=[(0,0,0),(1,0,0)]
        b=[(0,0,0),(2,0,0)]
        self.assertAlmostEqual(hausdorff_distance(a,b),1.0,places=7)

    def test_iou(self):
        a=[(0,0,0),(1,0,0)]
        b=[(1,0,0),(2,0,0)]
        self.assertAlmostEqual(volumetric_iou(a,b),1/3,places=7)

    def test_rms(self):
        self.assertAlmostEqual(rms_residual([1,2,3],[1,2,4]),(1/3)**0.5,places=7)

    def test_spin_error(self):
        self.assertAlmostEqual(spin_vector_angular_error_deg((1,0,0),(0,1,0)),90.0,places=7)


if __name__ == "__main__":
    unittest.main()
