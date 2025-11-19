#!/usr/bin/env python3
"""
Batch Gradient Flow Processor
Create sequences of stackable gradient flows with various configurations
"""

import os
import argparse
import json
from typing import List, Dict, Any
from gradientFlowGenerator import GradientFlowGenerator, create_stackable_sequence
from PIL import Image

class BatchProcessor:
    """Batch processor for creating gradient flow sequences"""
    
    def __init__(self, config_file: str = None):
        self.generator = GradientFlowGenerator()
        self.config = self.load_config(config_file) if config_file else self.default_config()
    
    def default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "color_schemes": {
                "frosty": [
                    "#1a3a52", "#2d5873", "#4a7c94", 
                    "#6ba3b5", "#8cc8d8", "#3d6b7d"
                ],
                "sunset": [
                    "#1a1a2e", "#16213e", "#0f3460",
                    "#533483", "#c74177", "#ee9595"
                ],
                "ocean": [
                    "#051937", "#004d6d", "#00718f",
                    "#0094a8", "#00b5b8", "#7dd5c0"
                ],
                "monochrome": [
                    "#1a1a1a", "#2d2d2d", "#404040",
                    "#595959", "#737373", "#8c8c8c"
                ],
                "forest": [
                    "#1b3a26", "#2d5a3d", "#3e7553",
                    "#4f906a", "#60ab80", "#71c697"
                ]
            },
            "sequences": [
                {
                    "name": "smooth_transition",
                    "count": 6,
                    "params": {
                        "noise_scale": 0.002,
                        "noise_amplitude": 0.08,
                        "wave_count": 2,
                        "wave_amplitude": 40
                    }
                },
                {
                    "name": "dynamic_flow",
                    "count": 8,
                    "params": {
                        "noise_scale": 0.004,
                        "noise_amplitude": 0.15,
                        "wave_count": 4,
                        "wave_amplitude": 60
                    }
                },
                {
                    "name": "minimal",
                    "count": 4,
                    "params": {
                        "noise_scale": 0.001,
                        "noise_amplitude": 0.05,
                        "wave_count": 1,
                        "wave_amplitude": 20
                    }
                }
            ],
            "output": {
                "width": 1080,
                "height": 1920,
                "format": "png",
                "quality": 95
            }
        }
    
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def save_config(self, config_file: str):
        """Save current configuration to JSON file"""
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def create_sequence(self, 
                       colors: List[str],
                       sequence_name: str,
                       output_dir: str,
                       sequence_config: Dict[str, Any] = None) -> List[str]:
        """
        Create a sequence of gradient flows
        
        Args:
            colors: List of hex colors
            sequence_name: Name for the sequence
            output_dir: Output directory
            sequence_config: Configuration for the sequence
        
        Returns:
            List of generated file paths
        """
        if sequence_config is None:
            sequence_config = {
                "count": 6,
                "params": {
                    "noise_scale": 0.003,
                    "noise_amplitude": 0.1,
                    "wave_count": 3,
                    "wave_amplitude": 50
                }
            }
        
        # Create output directory
        sequence_dir = os.path.join(output_dir, sequence_name)
        os.makedirs(sequence_dir, exist_ok=True)
        
        # Generate sequence
        generator = GradientFlowGenerator(
            self.config["output"]["width"],
            self.config["output"]["height"]
        )
        
        file_paths = []
        count = sequence_config["count"]
        params = sequence_config["params"]
        
        for i in range(count):
            # Calculate color transition
            color_progress = i / max(count - 1, 1)
            
            # Alternate between dark-to-light and light-to-dark
            if i % 2 == 0:
                # Dark to light transition
                start_idx = int(color_progress * (len(colors) - 1))
                end_idx = min(start_idx + 1, len(colors) - 1)
            else:
                # Light to dark transition
                end_idx = int(color_progress * (len(colors) - 1))
                start_idx = min(end_idx + 1, len(colors) - 1)
            
            start_color = colors[start_idx]
            end_color = colors[end_idx]
            
            # Vary parameters slightly for each image
            variation_factor = 1 + (i % 3) * 0.1
            
            # Generate image
            img = generator.generate_flow(
                start_color=start_color,
                end_color=end_color,
                flow_direction=['vertical', 'diagonal', 'horizontal'][i % 3],
                noise_scale=params["noise_scale"] * variation_factor,
                noise_amplitude=params["noise_amplitude"],
                wave_count=params["wave_count"] + (i % 2),
                wave_amplitude=int(params["wave_amplitude"] * variation_factor)
            )
            
            # Save image
            filename = f"{sequence_name}_{i+1:03d}.{self.config['output']['format']}"
            filepath = os.path.join(sequence_dir, filename)
            
            if self.config["output"]["format"].lower() in ['jpg', 'jpeg']:
                img.save(filepath, quality=self.config["output"]["quality"])
            else:
                img.save(filepath)
            
            file_paths.append(filepath)
            print(f"Generated: {filepath}")
        
        return file_paths
    
    def create_transition_pair(self,
                              color1: str,
                              color2: str,
                              output_dir: str,
                              pair_name: str = "transition") -> tuple:
        """
        Create a pair of images that transition smoothly
        Perfect for creating seamless loops
        
        Args:
            color1: First color
            color2: Second color
            output_dir: Output directory
            pair_name: Name for the pair
        
        Returns:
            Tuple of file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        generator = GradientFlowGenerator(
            self.config["output"]["width"],
            self.config["output"]["height"]
        )
        
        # First image: color1 to color2
        img1 = generator.generate_flow(
            start_color=color1,
            end_color=color2,
            flow_direction='vertical',
            noise_scale=0.003,
            noise_amplitude=0.1,
            wave_count=3,
            wave_amplitude=50
        )
        
        # Second image: color2 to color1 (reverse)
        img2 = generator.generate_flow(
            start_color=color2,
            end_color=color1,
            flow_direction='vertical',
            noise_scale=0.003,
            noise_amplitude=0.1,
            wave_count=3,
            wave_amplitude=50
        )
        
        # Save images
        path1 = os.path.join(output_dir, f"{pair_name}_forward.png")
        path2 = os.path.join(output_dir, f"{pair_name}_reverse.png")
        
        img1.save(path1)
        img2.save(path2)
        
        print(f"Created transition pair: {path1}, {path2}")
        return path1, path2
    
    def create_grid_preview(self,
                           image_paths: List[str],
                           output_path: str,
                           grid_size: tuple = (3, 2),
                           thumb_size: tuple = (180, 320)):
        """
        Create a grid preview of multiple images
        
        Args:
            image_paths: List of image file paths
            output_path: Output path for the grid
            grid_size: (columns, rows) for the grid
            thumb_size: Size of each thumbnail
        """
        cols, rows = grid_size
        width = cols * thumb_size[0]
        height = rows * thumb_size[1]
        
        grid_img = Image.new('RGB', (width, height), color='black')
        
        for idx, img_path in enumerate(image_paths[:cols * rows]):
            if os.path.exists(img_path):
                img = Image.open(img_path)
                img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
                
                col = idx % cols
                row = idx // cols
                
                x = col * thumb_size[0]
                y = row * thumb_size[1]
                
                grid_img.paste(img, (x, y))
        
        grid_img.save(output_path)
        print(f"Created grid preview: {output_path}")
    
    def process_all_schemes(self, output_dir: str = "gradient_output"):
        """Process all color schemes with all sequence configurations"""
        
        for scheme_name, colors in self.config["color_schemes"].items():
            print(f"\nProcessing color scheme: {scheme_name}")
            scheme_dir = os.path.join(output_dir, scheme_name)
            
            for sequence in self.config["sequences"]:
                print(f"  Creating sequence: {sequence['name']}")
                paths = self.create_sequence(
                    colors=colors,
                    sequence_name=sequence["name"],
                    output_dir=scheme_dir,
                    sequence_config=sequence
                )
                
                # Create preview grid for this sequence
                grid_path = os.path.join(scheme_dir, f"{sequence['name']}_preview.jpg")
                self.create_grid_preview(paths, grid_path)
        
        print(f"\nAll sequences generated in: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Batch process gradient flows")
    parser.add_argument('--config', type=str, help='Configuration JSON file')
    parser.add_argument('--output', type=str, default='gradient_output', help='Output directory')
    parser.add_argument('--scheme', type=str, help='Color scheme name')
    parser.add_argument('--sequence', type=str, help='Sequence name')
    parser.add_argument('--colors', nargs='+', help='Custom colors (hex)')
    parser.add_argument('--count', type=int, default=6, help='Number of images')
    parser.add_argument('--create-config', action='store_true', help='Create default config file')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = BatchProcessor(args.config)
    
    if args.create_config:
        processor.save_config('gradient_config.json')
        print("Created default configuration file: gradient_config.json")
        return
    
    if args.colors:
        # Use custom colors
        print(f"Using custom colors: {args.colors}")
        sequence_name = args.sequence or "custom_sequence"
        
        paths = processor.create_sequence(
            colors=args.colors,
            sequence_name=sequence_name,
            output_dir=args.output,
            sequence_config={
                "count": args.count,
                "params": {
                    "noise_scale": 0.003,
                    "noise_amplitude": 0.1,
                    "wave_count": 3,
                    "wave_amplitude": 50
                }
            }
        )
        
        # Create preview
        preview_path = os.path.join(args.output, f"{sequence_name}_preview.jpg")
        processor.create_grid_preview(paths, preview_path)
        
    elif args.scheme:
        # Use specific color scheme
        if args.scheme in processor.config["color_schemes"]:
            colors = processor.config["color_schemes"][args.scheme]
            sequence_name = args.sequence or "default_sequence"
            
            paths = processor.create_sequence(
                colors=colors,
                sequence_name=sequence_name,
                output_dir=args.output,
                sequence_config={
                    "count": args.count,
                    "params": {
                        "noise_scale": 0.003,
                        "noise_amplitude": 0.1,
                        "wave_count": 3,
                        "wave_amplitude": 50
                    }
                }
            )
            
            # Create preview
            preview_path = os.path.join(args.output, f"{sequence_name}_preview.jpg")
            processor.create_grid_preview(paths, preview_path)
        else:
            print(f"Unknown color scheme: {args.scheme}")
            print(f"Available schemes: {list(processor.config['color_schemes'].keys())}")
    else:
        # Process all schemes
        processor.process_all_schemes(args.output)


if __name__ == "__main__":
    main()