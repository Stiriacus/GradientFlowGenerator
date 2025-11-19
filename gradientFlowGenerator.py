#!/usr/bin/env python3
"""
Gradient Flow Generator with Perlin Noise
Creates smooth, flowing gradient images that can be stacked together
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import colorsys
from typing import Tuple, List, Optional
import math

class PerlinNoise:
    """Simple Perlin noise implementation for smooth random values"""
    
    def __init__(self, seed=0):
        np.random.seed(seed)
        self.permutation = self._generate_permutation()
        
    def _generate_permutation(self):
        p = np.arange(256, dtype=int)
        np.random.shuffle(p)
        return np.concatenate([p, p])
    
    def _fade(self, t):
        """Fade function for smooth interpolation"""
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def _lerp(self, t, a, b):
        """Linear interpolation"""
        return a + t * (b - a)
    
    def _grad(self, hash_val, x, y):
        """Generate gradient vectors"""
        h = hash_val & 3
        u = x if h < 2 else y
        v = y if h < 2 else x
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)
    
    def noise(self, x, y):
        """Generate 2D Perlin noise"""
        X = int(np.floor(x)) & 255
        Y = int(np.floor(y)) & 255
        
        x -= np.floor(x)
        y -= np.floor(y)
        
        u = self._fade(x)
        v = self._fade(y)
        
        A = self.permutation[X] + Y
        AA = self.permutation[A]
        AB = self.permutation[A + 1]
        B = self.permutation[X + 1] + Y
        BA = self.permutation[B]
        BB = self.permutation[B + 1]
        
        res = self._lerp(v,
                        self._lerp(u, self._grad(self.permutation[AA], x, y),
                                     self._grad(self.permutation[BA], x - 1, y)),
                        self._lerp(u, self._grad(self.permutation[AB], x, y - 1),
                                     self._grad(self.permutation[BB], x - 1, y - 1)))
        
        return (res + 1) / 2  # Normalize to 0-1

class GradientFlowGenerator:
    """Generate flowing gradient images with customizable parameters"""
    
    def __init__(self, width=1080, height=1920):
        self.width = width
        self.height = height
        self.perlin = PerlinNoise()
        
    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color"""
        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
    
    def interpolate_color(self, color1: Tuple[int, int, int], 
                          color2: Tuple[int, int, int], 
                          t: float) -> Tuple[int, int, int]:
        """Interpolate between two colors using HSV for smoother transitions"""
        # Convert to HSV for better color interpolation
        hsv1 = colorsys.rgb_to_hsv(color1[0]/255, color1[1]/255, color1[2]/255)
        hsv2 = colorsys.rgb_to_hsv(color2[0]/255, color2[1]/255, color2[2]/255)
        
        # Interpolate in HSV space
        h = hsv1[0] + t * (hsv2[0] - hsv1[0])
        s = hsv1[1] + t * (hsv2[1] - hsv1[1])
        v = hsv1[2] + t * (hsv2[2] - hsv1[2])
        
        # Convert back to RGB
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
    
    def generate_flow(self, 
                     start_color: str,
                     end_color: str,
                     flow_direction: str = 'vertical',
                     noise_scale: float = 0.003,
                     noise_amplitude: float = 0.15,
                     wave_count: int = 3,
                     wave_amplitude: float = 50,
                     gradient_stops: List[float] = None) -> Image.Image:
        """
        Generate a flowing gradient image
        
        Args:
            start_color: Starting hex color (e.g., '#1a2b3c')
            end_color: Ending hex color
            flow_direction: 'vertical', 'horizontal', or 'diagonal'
            noise_scale: Scale of Perlin noise (smaller = smoother)
            noise_amplitude: Strength of noise effect (0-1)
            wave_count: Number of wave undulations
            wave_amplitude: Amplitude of wave effect in pixels
            gradient_stops: Optional list of stop positions (0-1) for multi-stop gradient
        
        Returns:
            PIL Image object
        """
        # Create base image
        img = Image.new('RGB', (self.width, self.height))
        pixels = img.load()
        
        # Convert colors
        rgb_start = self.hex_to_rgb(start_color)
        rgb_end = self.hex_to_rgb(end_color)
        
        # Generate gradient with flow
        for y in range(self.height):
            for x in range(self.width):
                # Calculate base gradient position
                if flow_direction == 'vertical':
                    base_t = y / self.height
                elif flow_direction == 'horizontal':
                    base_t = x / self.width
                else:  # diagonal
                    base_t = (x + y) / (self.width + self.height)
                
                # Add wave distortion
                wave_offset = 0
                if wave_count > 0:
                    if flow_direction == 'vertical':
                        wave_offset = math.sin(x / self.width * math.pi * wave_count) * wave_amplitude / self.height
                    elif flow_direction == 'horizontal':
                        wave_offset = math.sin(y / self.height * math.pi * wave_count) * wave_amplitude / self.width
                    else:
                        wave_offset = math.sin((x + y) / (self.width + self.height) * math.pi * wave_count) * wave_amplitude / (self.width + self.height)
                
                # Add Perlin noise
                noise_value = self.perlin.noise(x * noise_scale, y * noise_scale)
                noise_offset = (noise_value - 0.5) * noise_amplitude
                
                # Combine all effects
                t = base_t + wave_offset + noise_offset
                t = max(0, min(1, t))  # Clamp to 0-1
                
                # Apply gradient stops if provided
                if gradient_stops:
                    # Multi-stop gradient logic
                    for i in range(len(gradient_stops) - 1):
                        if t <= gradient_stops[i + 1]:
                            local_t = (t - gradient_stops[i]) / (gradient_stops[i + 1] - gradient_stops[i])
                            color = self.interpolate_color(rgb_start, rgb_end, local_t)
                            break
                    else:
                        color = rgb_end
                else:
                    # Simple two-color gradient
                    color = self.interpolate_color(rgb_start, rgb_end, t)
                
                pixels[x, y] = color
        
        # Apply subtle blur for smoother transitions
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        
        return img
    
    def generate_multi_layer_flow(self,
                                 colors: List[str],
                                 layer_count: int = 3,
                                 opacity_range: Tuple[float, float] = (0.3, 0.7)) -> Image.Image:
        """
        Generate multiple overlapping flow layers for more complex effects
        
        Args:
            colors: List of hex colors to use
            layer_count: Number of layers to generate
            opacity_range: Min and max opacity for layers
        
        Returns:
            Composite PIL Image
        """
        base_img = None
        
        for i in range(layer_count):
            # Cycle through colors
            start_idx = i % len(colors)
            end_idx = (i + 1) % len(colors)
            
            # Vary parameters for each layer
            layer = self.generate_flow(
                start_color=colors[start_idx],
                end_color=colors[end_idx],
                flow_direction=['vertical', 'horizontal', 'diagonal'][i % 3],
                noise_scale=0.002 + i * 0.001,
                noise_amplitude=0.1 + i * 0.05,
                wave_count=2 + i,
                wave_amplitude=30 + i * 10
            )
            
            if base_img is None:
                base_img = layer
            else:
                # Blend layers
                opacity = opacity_range[0] + (opacity_range[1] - opacity_range[0]) * (i / layer_count)
                base_img = Image.blend(base_img, layer, opacity)
        
        return base_img


def create_stackable_sequence(colors: List[str], 
                             image_count: int,
                             width: int = 1080,
                             height: int = 1920,
                             output_prefix: str = "flow") -> List[Image.Image]:
    """
    Create a sequence of stackable gradient flows
    
    Args:
        colors: List of hex colors to cycle through
        image_count: Number of images to generate
        width: Image width
        height: Image height
        output_prefix: Prefix for saved files
    
    Returns:
        List of PIL Images
    """
    generator = GradientFlowGenerator(width, height)
    images = []
    
    for i in range(image_count):
        # Ensure smooth transitions between images
        start_color_idx = i % len(colors)
        end_color_idx = (i + 1) % len(colors)
        
        # Alternate between dark-to-light and light-to-dark
        if i % 2 == 0:
            start_color = colors[start_color_idx]
            end_color = colors[end_color_idx]
        else:
            start_color = colors[end_color_idx]
            end_color = colors[start_color_idx]
        
        # Vary parameters for each image
        img = generator.generate_flow(
            start_color=start_color,
            end_color=end_color,
            flow_direction=['vertical', 'diagonal', 'vertical'][i % 3],
            noise_scale=0.002 + (i % 3) * 0.001,
            noise_amplitude=0.1 + (i % 3) * 0.05,
            wave_count=2 + (i % 4),
            wave_amplitude=40 + (i % 3) * 20
        )
        
        # Save individual image
        filename = f"{output_prefix}_{i+1:03d}.png"
        img.save(filename)
        print(f"Saved: {filename}")
        
        images.append(img)
    
    return images


# Example usage
if __name__ == "__main__":
    # Your frosty colors palette
    frosty_colors = [
        '#1a3a52',  # Deep blue
        '#2d5873',  # Medium blue
        '#4a7c94',  # Light blue
        '#6ba3b5',  # Cyan blue
        '#8cc8d8',  # Light cyan
        '#3d6b7d',  # Teal
    ]
    
    # Generate a single flow
    generator = GradientFlowGenerator()
    
    # Example 1: Simple two-color flow
    img1 = generator.generate_flow(
        start_color='#1a3a52',
        end_color='#8cc8d8',
        flow_direction='vertical',
        noise_scale=0.003,
        noise_amplitude=0.15,
        wave_count=3,
        wave_amplitude=50
    )
    img1.save('single_flow.png')
    print("Generated: single_flow.png")
    
    # Example 2: Multi-layer complex flow
    img2 = generator.generate_multi_layer_flow(
        colors=frosty_colors,
        layer_count=3,
        opacity_range=(0.3, 0.7)
    )
    img2.save('multi_layer_flow.png')
    print("Generated: multi_layer_flow.png")
    
    # Example 3: Create stackable sequence
    sequence = create_stackable_sequence(
        colors=frosty_colors,
        image_count=6,
        output_prefix='stackable_flow'
    )
    print(f"Generated {len(sequence)} stackable images")