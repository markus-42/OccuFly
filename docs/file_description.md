## Ground Truth Masks (`ground_truth/{frame_id}/`)
Each frame directory contains the following files:

#### 1. **`{frame_id}.label`**
- **Format**: Binary file, uint8, flattened array
- **Shape**: `(192 × 128 × 128,)` = 3,145,728 voxels
- **Reshapes to**: `(192, 128, 128)` → (Width, Height, Depth)
- **Content**: Semantic class ID for each voxel
  - `0` = empty space
  - `1-36` = semantic classes (road, building, vegetation, etc.)
  - `255` = invalid/unknown (outside valid bounds or no data)
- **Note**: Already in **camera coordinate system**

#### 2. **`{frame_id}.invalid`**
- **Format**: Binary file, bitpacked boolean array
- **Shape**: Unpacks to `(192, 128, 128)`
- **Content**: Invalid mask (1 = invalid, 0 = valid)
- **Note**: Marks voxels outside valid frustum bounds or with uncertain data

#### 3. **`{frame_id}.occluded`**
- **Format**: Binary file, bitpacked boolean array
- **Shape**: Unpacks to `(192, 128, 128)`
- **Content**: Occlusion mask (1 = occluded from camera, 0 = visible)

#### 4. **`{frame_id}.surface`**
- **Format**: Binary file, bitpacked boolean array
- **Shape**: Unpacks to `(192, 128, 128)`
- **Content**: Surface voxel mask (1 = surface voxel, 0 = interior/non-surface)
- **Note**: Voxels with at least one unoccupied or void neighbor

## Preprocessed Files (`preprocess/{frame_id}.pkl`)

Each pickle file contains a dictionary with the following keys:

```python
{
    # Metadata
    'frame_id': str,              # e.g., '000000'
    'sequence': str,              # e.g., 'scene_01'
    'altitude': int,              # e.g., 30, 40, or 50 (meters)
    
    # Camera pose (4x4 homogeneous matrix)
    'pose': np.ndarray,           # Shape: (4, 4), dtype: float32
                                  # Note: local (arbitrary) coordinate system
                                  # Frustum grids are already in camera coords
    
    # Multi-resolution semantic labels (with invalid mask applied)
    '1_1': np.ndarray,            # Full resolution: (192, 128, 128)
    '1_2': np.ndarray,            # 2x downsampled: (96, 64, 64)
    '1_4': np.ndarray,            # 4x downsampled: (48, 32, 32)
    '1_8': np.ndarray,            # 8x downsampled: (24, 16, 16)
    '1_16': np.ndarray,           # 16x downsampled: (12, 8, 8)
}
```

**Key Points**:
- All downsampled grids use **majority pooling** (most common non-empty class in each pool)
- Invalid masks are **already applied** (invalid voxels set to 255)
- Grids are in **camera coordinate system** (frustum-aligned)
- `dtype`: uint8 for all label arrays

## Camera Calibration File (`calibration.txt`)

**`calibration.txt`**
- **Format**: txt file
- **Content**: Camera intrinsic parameters
  - Focal length (fx, fy)
  - Principal point (cx, cy)
  - Image dimensions



## Ground-Truth Depth Maps (`depth_maps/{frame_id}.npy`)

- **Format**: flattened NumPy binary file (.npy) 
- **Resolution**: 1/4 of the original RGB image resolution (e.g., 1368 x 912 if original is 5472 x 3648) )
- **Content**: Per-pixel metric depth values (in meters) from the camera perspective
- **Zero Depth**: Since depth maps have been constructed using classical 3D reconstruction, not all pixels have depth values. Instead, these pixels carry zero.
- **Large Depth Values**: Due to minor inconsitencies during data generation, some depth values exceed reasonable limits. These values have not been removed, but can handled during data loading.
- **Coordinate System**: Camera coordinate system (aligned with RGB images).
- **Usage**: Can be used for validation, depth supervision, or auxiliary tasks.



## Predicted Depth Maps (`OccuFly_Predicted_DepthMaps/.../depth_maps/{frame_id}.npy`)

These are **predicted depth estimates** obtained by our fine-tuned **Depth Anything v2** model on the OccuFly dataset.

- **Model**: [Depth Anything v2](https://github.com/DepthAnything/Depth-Anything-V2) (fine-tuned on OccuFly)
- **Format**: flattened NumPy binary file (.npy)
- **Resolution**: 1/4 of the original RGB image resolution (same as ground-truth depth maps)
- **Content**: Per-pixel depth predictions for the entire image
- **Advantage**: Unlike ground-truth depth maps, these predictions have estimates even in occluded or challenging regions
- **Usage**: Can serve as additional training signal, initialization, or comparison baseline for 3D occupancy prediction tasks
