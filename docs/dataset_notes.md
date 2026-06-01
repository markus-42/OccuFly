## Overall Attributes
- 20,611 samples: each consisting of an RGB image, a semantic occupancy grid, and a metric depth map
- 9 scenes
- 3 altitudes: 50m, 30m, 30m
- 21 semantic categories
- 4 seasons
- 3 environments: urban, industrial, rural
- 2 camera systems
- 3 camera perspectives: 0° (top-down), 15° tilt, 20° tilt

See below, or refer to the [OccuFly Paper (incl. the appendix)](https://arxiv.org/abs/2512.20770) for more details on these attributes. 


## Voxel Grid Specifications

| Parameter          | Value                  |
|--------------------|------------------------|
| Grid Dimensions    | 192 × 128 × 128 (W×H×D)|
| Voxel Size         | 0.5 meters             |
| Coordinate System  | Camera-centric frustum |
| Origin             | Camera position (0,0,0)|
| X-axis (Width)     | Camera right           |
| Y-axis (Height)    | Camera down            |
| Z-axis (Depth)     | Camera forward         |
| Total Voxels       | 3,145,728 per frame    |
| Physical Coverage  | 96m × 64m × 64m        |


## Semantic Classes

| ID | Class | Frequency [%] | Color (RGB) |
|----|-------|---------------|-------------|
| 1 | Road | 1.8909 | [128, 0, 128] |
| 2 | Walkway | 2.0610 | [204, 163, 72] |
| 3 | Dirt | 2.3584 | [128, 0, 0] |
| 4 | Gravel | 1.4511 | [192, 192, 192] |
| 5 | Rock | 0.0402 | [246, 120, 40] |
| 6 | Grass | 8.5614 | [0, 255, 0] |
| 7 | Vegetation | 4.3121 | [112, 148, 32] |
| 8 | Tree | 7.5479 | [64, 64, 0] |
| 9 | Ground Obstacle | 1.9605 | [255, 255, 0] |
| 11 | Person | 0.0001 | [255, 16, 255] |
| 12 | Bicycle | 0.0035 | [255, 204, 153] |
| 13 | Vehicle | 0.5683 | [0, 128, 128] |
| 14 | Water | 1.7539 | [0, 0, 255] |
| 16 | Building | 62.1534 | [255, 0, 0] |
| 17 | Roof | 2.2018 | [64, 160, 120] |
| 21 | Cable | 0.0018 | [255, 160, 0] 
| 22 | Cable Tower | 0.0047 | [106, 0, 255] |
| 33 | Parking Lot | 2.8415 | [128, 64, 128] |
| 34 | Construction | 0.2741 | [240, 120, 120] |
| 35 | Crane | 0.0059 | [255, 255, 128] |
| 36 | Truck | 0.1105 | [128, 128, 64] |

#### Special Classes
- **0**: empty (unoccupied space)
- **255**: invalid/unknown (outside valid bounds)


## Coordinate System
- **Frustum grids are already in camera coordinate system**
- Camera is at origin (0, 0, 0)
- No transformation needed when using frustum grids
- Poses are given in a local (arbitrary) coordinate system

## Grid Indexing
- **Array shape**: `(W, H, D)` = `(192, 128, 128)`
- **W (width)**: -48m to +48m (left to right, camera x-axis)
- **H (height)**: -32m to +32m (top to bottom, camera y-axis)
- **D (depth)**: 0m to 64m (near to far, camera z-axis)

## Invalid Mask Handling
- In raw files: separate `.invalid` file
- In preprocessed files: already applied (labels set to 255)
- Invalid voxels occur:
  - Outside valid frustum bounds
  - In occluded regions without surface information
  - Where 3D reconstruction failed during data generation

## Altitudes
Each scene covers 30m, 40m, and 50m heights


## Missing Frames:
Due to insufficient ground-truth and predicted depth for certain frames, a small number of samples were removed during dataset preparation. The enumerated files in the dataset have discontinuities at the following locations:

| Scene     | Altitude | Missing Frame |
|-----------|----------|---------------|
| scene_04  | 30m      | 001388        |
| scene_05  | 30m      | 001217        |
| scene_05  | 30m      | 001442        |
| scene_05  | 40m      | 000994        |
| scene_05  | 40m      | 001040        |

All files related to these frames (depth predictions, RGB images, ground truth, and preprocessed data) were removed from the dataset. The final dataset contains **20,611 samples**.