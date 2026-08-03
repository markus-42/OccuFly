## Dataset Splits

| Split      | Scenes                             
|------------|------------------------------------
| **Train**  | `scene_01` to `scene_05` (5 scenes)
| **Val**    | `scene_06` to `scene_07` (2 scenes)
| **Test**   | `scene_08` to `scene_09` (2 scenes)

**Total**: 9 scenes, each captured at 3 altitudes (30m, 40m, 50m)

## Dataset Structure

The directory structure for the OccuFly project is as follows:

```
OccuFly/
├── OccuFly_Dataset/
│   ├── scene_01/                        # Training scene 1
│   │   ├── calibration.txt              # Camera calibration parameters
│   │   ├── 30/                          # 30 meters altitude
│   │   │   ├── ground_truth/            # Raw voxel grid outputs
│   │   │   │   ├── 000000/              # Frame 000000
│   │   │   │   │   ├── 000000.label         # Semantic labels (uint8, flattened)
│   │   │   │   │   ├── 000000.invalid       # Invalid mask (bitpacked)
│   │   │   │   │   ├── 000000.occluded      # Occlusion mask (bitpacked)
│   │   │   │   │   ├── 000000.surface       # Surface voxels mask (bitpacked)
│   │   │   │   ├── 000001/              # Frame 000001
│   │   │   │   │   └── ...
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── preprocess/              # Preprocessed pickle files
│   │   │   │   ├── 000000.pkl               # Preprocessed data for frame 000000
│   │   │   │   ├── 000001.pkl               # Preprocessed data for frame 000001
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── images/                  # RGB camera images
│   │   │   │   └── visual/
│   │   │   │       ├── 000000.png
│   │   │   │       ├── 000001.png
│   │   │   │       └── ...
│   │   │   │
│   │   │   ├── depth_maps/              # Depth maps (flattened, in meters, 1/4 resolution of images)
│   │   │   │   ├── 000000.npy
│   │   │   │   └── ...
│   │   │
│   │   ├── 40/                          # 40 meters altitude
│   │   │   └── (same structure as 30/)
│   │   │
│   │   └── 50/                          # 50 meters altitude
│   │       └── (same structure as 30/)
│   │
│   ├── scene_[02-09]/                        # Training scenes 2-9
│       └── (same structure as scene_01)
│
│
└── OccuFly_Predicted_DepthMaps/         # (optional) Predicted depth maps obtained by our fine-tuning Depth Anything v2
    ├── scene_01/                        # Training scene 1
    │   ├── 30/                          # 30 meters altitude
    │   │   └── depth_maps/              # Predicted depth maps
    │   │       ├── 000000.npy
    │   │       └── ...
    │   │
    │   ├── 40/                          # 40 meters altitude
    │   │   └── depth_maps/
    │   │       └── (same structure as 30/)
    │   │
    │   └── 50/                          # 50 meters altitude
    │       └── depth_maps/
    │           └── (same structure as 30/)
    │
    ├── scene_[02-09]/                        # Training scenes 2-9
    │   └── (same structure as scene_01)
```

