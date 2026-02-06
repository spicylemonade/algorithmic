# Metrics and Confidence Framework

Implemented in `src/lci/metrics.py`:
- Normalized Hausdorff distance (`normalized_hausdorff`)
- Volumetric IoU proxy (`bbox_iou`)
- Lightcurve RMSE (`lightcurve_rmse`)
- Pole-angle error in degrees (`pole_angle_error_deg`)
- Calibrated confidence score in `[0,1]` (`calibrated_confidence`)

Threshold rules:
- High confidence: `score >= 0.8`
- Medium confidence: `0.6 <= score < 0.8`
- Low confidence: `0.4 <= score < 0.6`
- Validation pass condition tied to deviation criterion: `normalized_hausdorff <= 0.05`
