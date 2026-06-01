import os
import argparse
import numpy as np
import cv2
import open3d as o3d
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import tkinter as tk
from pathlib import Path

GRID_DIM = (192, 128, 128)
VOXEL_SIZE = 0.5

# Semantic color mapping (OccuFly classes)
ID2COLOR = {
    0:   [0, 0, 0],           # empty
    1:   [128, 0, 128],       # road
    2:   [204, 163, 72],      # walkway
    3:   [128, 0, 0],         # dirt
    4:   [192, 192, 192],     # gravel
    5:   [246, 120, 40],      # rock
    6:   [0, 255, 0],         # grass
    7:   [112, 148, 32],      # vegetation
    8:   [64, 64, 0],         # tree
    9:   [255, 255, 0],       # ground_obstacle
    11:  [255, 16, 255],      # person
    12:  [255, 204, 153],     # bicycle
    13:  [0, 128, 128],       # vehicle
    14:  [0, 0, 255],         # water
    16:  [255, 0, 0],         # building
    17:  [64, 160, 120],      # roof
    21:  [255, 160, 0],       # cable
    22:  [106, 0, 255],       # cable_tower
    33:  [128, 64, 128],      # parking_lot
    34:  [240, 120, 120],     # construction
    35:  [255, 255, 128],     # crane
    36:  [128, 128, 64],      # truck
}

class DataCache:
    """Cache for voxel grids."""
    def __init__(self):
        self.cache = {}
    
    def get(self, key):
        return self.cache.get(key)
    
    def set(self, key, value):
        self.cache[key] = value
    
    def clear(self):
        self.cache.clear()

_cache = DataCache()

def resize_image_maintain_aspect(img, target_h, target_w):
    """Resize image maintaining aspect ratio, pad with gray if needed."""
    if img is None:
        return None
    
    img_h, img_w = img.shape[:2]
    aspect_ratio = img_w / img_h
    target_aspect = target_w / target_h
    
    if aspect_ratio > target_aspect:
        new_w = target_w
        new_h = int(target_w / aspect_ratio)
    else:
        new_h = target_h
        new_w = int(target_h * aspect_ratio)
    
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    if len(resized.shape) == 3:
        canvas = np.full((target_h, target_w, resized.shape[2]), 128, dtype=resized.dtype)
    else:
        canvas = np.full((target_h, target_w), 128, dtype=resized.dtype)
    
    y_offset = (target_h - new_h) // 2
    x_offset = (target_w - new_w) // 2
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    
    return canvas

def load_labels(path, grid_dims):
    """Load label file with error handling."""
    if not os.path.exists(path):
        return None
    try:
        data = np.fromfile(path, dtype=np.uint8)
        return data.reshape(grid_dims)
    except Exception as e:
        print(f"Error loading labels from {path}: {e}")
        return None

def load_mask(path, grid_dims):
    """Load bitpacked mask file with error handling."""
    if not os.path.exists(path):
        return None
    try:
        data = np.fromfile(path, dtype=np.uint8)
        bit_mask = np.unpackbits(data)[:np.prod(grid_dims)]
        return bit_mask.reshape(grid_dims).astype(bool)
    except Exception as e:
        print(f"Error loading mask from {path}: {e}")
        return None

def build_fast_voxel_geometry(label_grid, mask, use_cache=True):
    """Build colored voxel grid from label and mask. Cached for performance."""
    if label_grid is None or mask is None:
        return None
    
    cache_key = (id(label_grid), id(mask))
    if use_cache and (cached := _cache.get(cache_key)):
        return cached
    
    valid_indices = np.argwhere(mask & (label_grid > 0))
    if len(valid_indices) == 0:
        return None

    W, H, D = GRID_DIM
    origin_shift = np.array([W // 2, H // 2, 0], dtype=np.int32)
    grid_coords = valid_indices - origin_shift
    labels = label_grid[valid_indices[:, 0], valid_indices[:, 1], valid_indices[:, 2]]
    
    voxels = []
    for coord, label in zip(grid_coords, labels):
        color = np.array(ID2COLOR.get(int(label), (255, 255, 255)), dtype=np.float32) / 255.0
        voxel = o3d.geometry.Voxel(grid_index=coord, color=color)
        voxels.append(voxel)
    
    voxel_grid = o3d.geometry.VoxelGrid()
    voxel_grid.voxel_size = VOXEL_SIZE
    for voxel in voxels:
        voxel_grid.add_voxel(voxel)
    
    if use_cache:
        _cache.set(cache_key, voxel_grid)
    
    return voxel_grid

_active_visualizer = None

def get_screen_size():
    """Detect screen resolution."""
    try:
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
        return screen_width, screen_height
    except:
        return 1920, 1080  # Default fallback

class OccuFlyVisualizer:
    def __init__(self, base_dir, scene, altitude, frame):
        self.base_dir = base_dir
        self.scene = scene
        self.altitude = str(altitude)
        self.frame = str(frame).zfill(6)  # Ensure 6-digit zero-padding
        
        self.screen_width, self.screen_height = get_screen_size()
        self.mask_types = ["surface", "occluded", "invalid", "occupancy"]
        self.current_mask_idx = 0
        self.voxel_geoms = {}
        self.active_visualizer = None
        self.shutdown_event = threading.Event()

        self.scene_path = os.path.join(base_dir, "OccuFly_Dataset", self.scene, self.altitude)
        self.gt_dir = os.path.join(self.scene_path, "ground_truth", self.frame)
        
        if not os.path.exists(self.gt_dir):
            raise FileNotFoundError(f"Ground truth directory not found: {self.gt_dir}")
        
        self.label_path = os.path.join(self.gt_dir, f"{self.frame}.label")
        self.labels = load_labels(self.label_path, GRID_DIM)
        if self.labels is None:
            raise ValueError(f"Failed to load labels from {self.label_path}")
        
        print(f"\n{'='*70}")
        print(f"OccuFly Ground Truth Visualizer")
        print(f"Scene: {self.scene} | Altitude: {self.altitude}m | Frame: {self.frame}")
        print(f"GT Directory: {self.gt_dir}")
        print(f"{'='*70}\n")
        
        print("Loading all mask geometries... (this may take a moment)")
        self._precompute_geometries()
        print("[OK] All masks loaded and ready!\n")
        self._load_and_display_2d()
        
    def _precompute_geometries(self):
        """Pre-compute all mask geometries for fast switching."""
        for i, mask_name in enumerate(self.mask_types):
            print(f"  [{i+1}/{len(self.mask_types)}] Loading {mask_name}...", end=" ", flush=True)
            
            if mask_name == "occupancy":
                mask = np.ones(GRID_DIM, dtype=bool)
            else:
                mask_path = os.path.join(self.gt_dir, f"{self.frame}.{mask_name}")
                mask = load_mask(mask_path, GRID_DIM)
                if mask is None:
                    print("[FAIL - file not found]")
                    continue
            
            voxel_geom = build_fast_voxel_geometry(self.labels, mask, use_cache=False)
            
            if voxel_geom is not None:
                self.voxel_geoms[mask_name] = voxel_geom
                print("[OK]")
            else:
                print("[FAIL - no valid voxels]")

    def _load_and_display_2d(self):
        """Load image and depth map, display on left side."""
        img_path = os.path.join(self.scene_path, "images", "visual", f"{self.frame}.png")
        depth_path = os.path.join(self.scene_path, "depth_maps", f"{self.frame}.npy")
        
        img_data = None
        if os.path.exists(img_path):
            try:
                img_data = cv2.imread(img_path)
                if img_data is not None:
                    img_data = cv2.cvtColor(img_data, cv2.COLOR_BGR2RGB)
                    print(f"[OK] Image loaded: {img_path}")
                    print(f"     Shape: {img_data.shape}")
                else:
                    print(f"[FAIL] Could not read image from {img_path}")
            except Exception as e:
                print(f"[FAIL] Error loading image: {e}")
        else:
            print(f"[FAIL] Image not found: {img_path}")

        depth_data = None
        if os.path.exists(depth_path):
            try:
                depth_data = np.load(depth_path)
                print(f"[OK] Depth map loaded: {depth_path}")
                print(f"     Original shape: {depth_data.shape}, Range: [{depth_data.min():.2f}, {depth_data.max():.2f}]")
                
                if depth_data.ndim == 1:
                    num_elements = len(depth_data)
                    possible_shapes = [(912, 1368), (576, 864)]  # Common OccuFly sizes
                    reshaped = False
                    for h, w in possible_shapes:
                        if h * w == num_elements:
                            depth_data = depth_data.reshape(h, w)
                            print(f"     Reshaped to: {depth_data.shape}")
                            reshaped = True
                            break
                    if not reshaped:
                        h = int(np.sqrt(num_elements * 3 / 4))
                        w = num_elements // h
                        depth_data = depth_data.reshape(h, w)
                        print(f"     Reshaped to: {depth_data.shape}")
            except Exception as e:
                print(f"[FAIL] Error loading depth map: {e}")
                depth_data = None
        else:
            print(f"[FAIL] Depth map not found: {depth_path}")
        
        if img_data is not None and depth_data is not None:
            depth_h, depth_w = depth_data.shape
            img_data = resize_image_maintain_aspect(img_data, depth_h, depth_w)
            print(f"     Resized image to {(depth_h, depth_w)}")
        elif img_data is not None and depth_data is None:
            print("[WARN] Image loaded but depth map missing")
        
        if img_data is not None or depth_data is not None:
            self._display_images_matplotlib(img_data, depth_data)

    def _display_images_matplotlib(self, img_data, depth_data):
        """Display images on left side with mask selection buttons."""
        self.depth_data = depth_data
        
        left_width_pixels = int(self.screen_width * 0.45)
        dpi = 100
        fig_width_inches = (left_width_pixels - 40) / dpi
        fig_height_inches = (self.screen_height - 100) / dpi
        
        fig = plt.figure(figsize=(fig_width_inches, fig_height_inches), dpi=dpi)
        self.fig = fig
        fig.suptitle(f"OccuFly - Scene : {self.scene} | Altitude : {self.altitude}m | Frame : {self.frame}", 
                     fontsize=12, fontweight='bold')
        
        gs = fig.add_gridspec(2, 1, height_ratios=[1.2, 1.0], hspace=0.3, top=0.92, bottom=0.15, left=0.08, right=0.92)
        ax_img = fig.add_subplot(gs[0])
        ax_depth = fig.add_subplot(gs[1])
        
        if img_data is not None:
            ax_img.imshow(img_data)
            ax_img.set_title("RGB Image", fontsize=11, fontweight='bold')
            ax_img.axis('off')
        else:
            ax_img.text(0.5, 0.5, 'Image not available', ha='center', va='center', transform=ax_img.transAxes)
            ax_img.set_title("RGB Image")
            ax_img.axis('off')
        
        if depth_data is not None:
            im = ax_depth.imshow(depth_data, cmap='plasma')
            ax_depth.set_title("Depth Map (Ground Truth)", fontsize=11, fontweight='bold')
            ax_depth.axis('off')
            cbar = plt.colorbar(im, ax=ax_depth, label='Depth (m)', pad=0.02, shrink=0.8)
            
            def on_motion(event):
                if event.inaxes == ax_depth and event.xdata and event.ydata:
                    x, y = int(event.xdata), int(event.ydata)
                    if 0 <= x < depth_data.shape[1] and 0 <= y < depth_data.shape[0]:
                        depth_val = depth_data[y, x]
                        fig.text(0.95, 0.95, f'Depth: {depth_val:.2f}m', 
                                ha='right', va='top', fontsize=9, 
                                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
                        fig.canvas.draw_idle()
            
            fig.canvas.mpl_connect('motion_notify_event', on_motion)
        else:
            ax_depth.text(0.5, 0.5, 'Depth map not available', ha='center', va='center', transform=ax_depth.transAxes)
            ax_depth.set_title("Depth Map (Ground Truth)")
            ax_depth.axis('off')
        
        button_width, button_height = 0.15, 0.04
        y_buttons_top, y_buttons_bottom = 0.08, 0.01
        buttons_x_positions = [0.08, 0.30, 0.52, 0.74]
        button_labels = ['Occupancy Grid', 'Invalid Mask', 'Surface Mask', 'Occluded Mask']
        button_to_mask_idx = [3, 2, 0, 1]
        
        self.buttons = []
        self.button_objects = {}
        
        for i, (label, x_pos) in enumerate(zip(button_labels, buttons_x_positions)):
            ax_btn = fig.add_axes([x_pos, y_buttons_top, button_width, button_height])
            btn = Button(ax_btn, label, color='lightgrey')
            mask_idx = button_to_mask_idx[i]
            btn.on_clicked(lambda e, idx=mask_idx: self._on_mask_button_clicked(idx))
            self.buttons.append(btn)
            self.button_objects[mask_idx] = btn
        
        ax_quit = fig.add_axes([0.40, y_buttons_bottom, button_width, button_height])
        btn_quit = Button(ax_quit, 'Quit', color='lightcoral')
        btn_quit.on_clicked(lambda e: self._quit_visualization())
        self.buttons.append(btn_quit)
        
        plt.tight_layout()
        plt.show()
        plt.pause(0.1)

    def _select_and_display_mask(self, mask_idx):
        """Select a mask and display in 3D."""
        print(f"\n[...] Loading mask {self.mask_types[mask_idx]}...")
        self.shutdown_event.set()
        time.sleep(0.3)
        self.shutdown_event.clear()
        self.current_mask_idx = mask_idx
        self._display_current_mask_in_thread()

    def _on_mask_button_clicked(self, mask_idx):
        """Handle button click and display mask."""
        self._update_button_colors(mask_idx)
        self._select_and_display_mask(mask_idx)

    def _update_button_colors(self, active_mask_idx):
        """Update button colors: active=green, others=grey."""
        if not hasattr(self, 'button_objects'):
            return
        for mask_idx, btn in self.button_objects.items():
            new_color = 'lightgreen' if mask_idx == active_mask_idx else 'lightgrey'
            btn.color = new_color
            for patch in btn.ax.patches:
                patch.set_facecolor(new_color)
        if hasattr(self, 'fig'):
            self.fig.canvas.draw_idle()

    def _quit_visualization(self):
        """Close all visualization windows."""
        plt.close('all')
        print("\n[OK] Visualization closed.")
        exit(0)

    def display_current_mask(self):
        """Display 3D voxel grid on right half of screen."""
        current_mask_name = self.mask_types[self.current_mask_idx]
        print(f"[{self.current_mask_idx+1}/{len(self.mask_types)}] Displaying: {current_mask_name.upper()}")
        
        if current_mask_name not in self.voxel_geoms:
            print(f"[FAIL] Geometry for {current_mask_name} not available")
            return
        
        voxel_geom = self.voxel_geoms[current_mask_name]
        
        try:
            vis = o3d.visualization.Visualizer()
            vis.create_window(window_name=f"OccuFly 3D - ({current_mask_name})", 
                             width=self.screen_width // 2, 
                             height=self.screen_height, 
                             left=self.screen_width // 2, 
                             top=0)
            
            self.active_visualizer = vis
            vis.add_geometry(voxel_geom)
            
            bounds = voxel_geom.get_axis_aligned_bounding_box()
            vis.get_view_control().set_front([0, 0, 1])
            vis.get_view_control().set_lookat(bounds.get_center())
            vis.get_view_control().set_up([0, -1, 0])
            
            while not self.shutdown_event.is_set():
                vis.poll_events()
                vis.update_renderer()
                time.sleep(0.01)
            
        except Exception as e:
            print(f"[ERROR] Visualizer error: {e}")
        finally:
            try:
                if self.active_visualizer:
                    self.active_visualizer.destroy_window()
                    self.active_visualizer = None
            except:
                pass
    
    def _display_current_mask_in_thread(self):
        """Display mask in separate thread."""
        thread = threading.Thread(target=self.display_current_mask, daemon=True)
        thread.start()

    def run(self):
        """Start visualization with first mask."""
        print("\n" + "="*70)
        print("VISUALIZATION INTERFACE:")
        print("  LEFT: Image and depth map | RIGHT: 3D voxel grid")
        print("  Click buttons to switch masks | Hover depth to see values")
        print("="*70 + "\n")
        print("[OK] Starting first mask visualization...")
        self._display_current_mask_in_thread()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OccuFly Ground Truth Multi-Modal Visualizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python visualize_gt.py --base_dir /path/to/OccuFly --scene scene_01 --altitude 30 --frame 000000
  python visualize_gt.py --base_dir /path/to/OccuFly --scene scene_02 --altitude 40 --frame 000015
        """
    )
    parser.add_argument("--base_dir", type=str, required=True, 
                        help="Path to OccuFly root directory")
    parser.add_argument("--scene", type=str, default="scene_01", 
                        help="Scene subfolder (default: scene_01)")
    parser.add_argument("--altitude", type=int, default=30, 
                        choices=[30, 40, 50],
                        help="Flight altitude in meters (default: 30)")
    parser.add_argument("--frame", type=str, default="000000", 
                        help="Frame ID with zero-padding (default: 000000)")
    
    args = parser.parse_args()

    try:
        app = OccuFlyVisualizer(args.base_dir, args.scene, args.altitude, args.frame)
        app.run()
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print(f"Ensure the directory structure exists and is properly formatted.")
        exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)