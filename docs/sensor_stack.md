## UAV Platforms

Monocular RGB images in the OccuFly dataset were captured using two DJI UAV platforms across 9 scenes.

| Platform | Scenes |
|---|---|
| [DJI Phantom 4 RTK](https://www.dji.com/de/support/product/phantom-4-rtk) | `scene_01`, `scene_02`, `scene_06`, `scene_07`, `scene_08` |
| [DJI Mavic 3 Enterprise](https://enterprise.dji.com/de/mavic-3-enterprise/specs) | `scene_03`, `scene_04`, `scene_05`, `scene_09` |

## Camera Specifications

**DJI Phantom 4 RTK:**

| Parameter | Value |
|---|---|
| Sensor | 1-inch CMOS |
| Resolution | 5472 × 3648 px (W × H) |
| Focal Length | 8.8 mm (35 mm equiv.: 24 mm) |
| Field of View | 84° |

<br>

**DJI Mavic 3 Enterprise:**
| Parameter | Value |
|---|---|
| Sensor | 1/2-inch CMOS |
| Resolution | 4000 × 3000 px (W × H) |
| Focal Length | 4.5 mm (35 mm equiv.: 24 mm) |
| Field of View | 84° |


## 3D Reconstruction Pipeline

3D reconstruction was performed using **[Agisoft Metashape](https://www.agisoftmetashape.com/)**, a standard photogrammetry tool widely used in UAV-based mapping workflows.

The pipeline consists of two main stages:

```
RGB Images  →  [1] Image Alignment  →  Sparse Point Cloud
                                              ↓
                               [2] Dense Point Cloud Generation
```

**Stage 1 — Image Alignment**
Camera poses are estimated from the RGB images via Structure-from-Motion (SfM), producing a sparse point cloud and calibrated camera parameters for each scene.

**Stage 2 — Dense Point Cloud Generation**
A dense point cloud is reconstructed from the aligned images using Multi-View Stereo (MVS), capturing fine-grained 3D geometry of the scene.

> **Tool:** Agisoft Metashape — [download here](https://www.agisoft.com/downloads/installer/)