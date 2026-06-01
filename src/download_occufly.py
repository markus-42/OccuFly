#!/usr/bin/env python3
"""
Simple script to download OccuFly dataset from Hugging Face Hub.

Downloads scene zips, predicted depths, and extracts them locally.

Usage:
    python download_occufly.py
    python download_occufly.py --split train
    python download_occufly.py --split validation
    python download_occufly.py --scenes 1 2 3
    python download_occufly.py --include_depth_predictions
    python download_occufly.py --only_depth_predictions
    python download_occufly.py --output ./my_data
"""

import sys
from pathlib import Path
import zipfile
import argparse

try:
    from huggingface_hub import hf_hub_download
    from tqdm import tqdm
except ImportError:
    print("Error: Required packages not installed.")
    print("Install with: pip install huggingface-hub tqdm")
    sys.exit(1)


class OccuFlyDownloader:
    """Download OccuFly dataset from HF Hub."""
    
    DATASET_ID = "markus-42/OccuFly"
    SCENES = list(range(1, 10))
    SPLITS = {
        "train": [1, 2, 3, 4, 5],
        "validation": [6, 7],
        "test": [8, 9]
    }
    
    def __init__(self, output_dir="./OccuFly", dataset_id=None):
        self.output_dir = Path(output_dir)
        self.dataset_id = dataset_id or self.DATASET_ID
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def download_scene(self, scene_num):
        """Download a scene zip."""
        if scene_num not in range(1, 10):
            raise ValueError(f"Invalid scene {scene_num}. Must be 1-9.")
        
        scene_name = f"scene_{scene_num:02d}"
        filename = f"OccuFly_Dataset/{scene_name}.zip"
        
        print(f"\n[DOWNLOAD] {scene_name}...")
        
        try:
            zip_path = hf_hub_download(
                repo_id=self.dataset_id,
                filename=filename,
                repo_type="dataset"
            )
            
            print(f"[EXTRACT] Extracting {scene_name}...")
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(self.output_dir)
            
            print(f"[OK] Scene extracted to: {self.output_dir / scene_name}")
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to download {scene_name}: {e}")
            return False
    
    def download_depth_predictions(self):
        """Download predicted depth maps."""
        filename = "OccuFly_Predicted_DepthMaps/OccuFly_Predicted_DepthMaps.zip"
        
        print(f"\n[DOWNLOAD] Predicted depth maps...")
        
        try:
            zip_path = hf_hub_download(
                repo_id=self.dataset_id,
                filename=filename,
                repo_type="dataset"
            )
            
            print(f"[EXTRACT] Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(self.output_dir)
            
            print(f"[OK] Predictions extracted to: {self.output_dir}")
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to download predictions: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Download OccuFly dataset from Hugging Face Hub"
    )
    parser.add_argument(
        "--split",
        choices=["train", "validation", "test"],
        help="Download a specific split (default: all splits)"
    )
    parser.add_argument(
        "--scenes",
        type=int,
        nargs="+",
        choices=range(1, 10),
        help="Scenes to download (default: all 1-9). Overrides --split if specified."
    )
    parser.add_argument(
        "--include_depth_predictions",
        action="store_true",
        help="Include predicted depth maps in download"
    )
    parser.add_argument(
        "--only_depth_predictions",
        action="store_true",
        help="Download only predicted depth maps"
    )
    parser.add_argument(
        "--output",
        default="./OccuFly",
        help="Output directory (default: ./OccuFly)"
    )
    parser.add_argument(
        "--dataset-id",
        default="markus-42/OccuFly",
        help="HF dataset ID"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("OccuFly Dataset Downloader")
    print("=" * 80)
    
    downloader = OccuFlyDownloader(
        output_dir=args.output,
        dataset_id=args.dataset_id
    )
    
    success = True
    
    if args.only_depth_predictions:
        success = downloader.download_depth_predictions()
    else:
        # Determine which scenes to download
        if args.scenes:
            # Explicit scenes take precedence
            scenes = args.scenes
        elif args.split:
            # Download specific split
            scenes = downloader.SPLITS[args.split]
        else:
            # Default: all scenes
            scenes = list(range(1, 10))
        
        print(f"\n[INFO] Downloading {len(scenes)} scenes...")
        print(f"[INFO] Output directory: {downloader.output_dir}")
        
        for scene_num in scenes:
            if not downloader.download_scene(scene_num):
                success = False
        
        # Download depth predictions if requested
        if args.include_depth_predictions:
            downloader.download_depth_predictions()
    
    print("\n" + "=" * 80)
    if success:
        print(f"[OK] Download complete!")
        print(f"Data saved to: {downloader.output_dir}")
    else:
        print("[ERROR] Some downloads failed")
    
    print("=" * 80)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
