#!/usr/bin/env python3
"""
Quick Gradient Generator
Simple command-line tool for generating gradient flows
"""

import argparse
import os
from gradientFlowGenerator import GradientFlowGenerator
from PIL import Image

def parse_color(color_str):
    """Parse color from various formats"""
    if color_str.startswith('#'):
        return color_str
    elif color_str.lower() in NAMED_COLORS:
        return NAMED_COLORS[color_str.lower()]
    else:
        # Try to add # if it looks like a hex code
        if len(color_str) == 6 and all(c in '0123456789abcdefABCDEF' for c in color_str):
            return f"#{color_str}"
        raise ValueError(f"Invalid color: {color_str}")

# Common named colors
NAMED_COLORS = {
    'black': '#000000',
    'white': '#ffffff',
    'red': '#ff0000',
    'green': '#00ff00',
    'blue': '#0000ff',
    'yellow': '#ffff00',
    'cyan': '#00ffff',
    'magenta': '#ff00ff',
    'gray': '#808080',
    'darkgray': '#404040',
    'lightgray': '#c0c0c0',
    'navy': '#000080',
    'teal': '#008080',
    'purple': '#800080',
    'orange': '#ffa500',
    'pink': '#ffc0cb',
    'brown': '#a52a2a',
    'darkblue': '#00008b',
    'lightblue': '#add8e6',
    'darkgreen': '#006400',
    'lightgreen': '#90ee90',
    'gold': '#ffd700',
    'silver': '#c0c0c0',
    'frosty': '#6ba3b5',
    'ocean': '#004d6d',
    'sunset': '#ee9595',
    'midnight': '#1a1a2e'
}

# Preset configurations
PRESETS = {
    'smooth': {
        'noise_scale': 0.002,
        'noise_amplitude': 0.05,
        'wave_count': 2,
        'wave_amplitude': 30,
        'description': 'Smooth, gentle gradients'
    },
    'wavy': {
        'noise_scale': 0.003,
        'noise_amplitude': 0.1,
        'wave_count': 5,
        'wave_amplitude': 80,
        'description': 'Wavy, flowing gradients'
    },
    'turbulent': {
        'noise_scale': 0.008,
        'noise_amplitude': 0.3,
        'wave_count': 7,
        'wave_amplitude': 120,
        'description': 'Turbulent, dynamic gradients'
    },
    'minimal': {
        'noise_scale': 0.001,
        'noise_amplitude': 0.02,
        'wave_count': 1,
        'wave_amplitude': 20,
        'description': 'Minimal, clean gradients'
    },
    'dunes': {
        'noise_scale': 0.004,
        'noise_amplitude': 0.15,
        'wave_count': 4,
        'wave_amplitude': 60,
        'description': 'Sand dune-like flowing gradients'
    },
    'silk': {
        'noise_scale': 0.0025,
        'noise_amplitude': 0.08,
        'wave_count': 3,
        'wave_amplitude': 45,
        'description': 'Silk fabric-like smooth gradients'
    }
}

def main():
    # Create epilog text separately
    epilog_text = """
Examples:
  # Generate a simple gradient
  quick_gradient.py -s "#1a3a52" -e "#8cc8d8" -o gradient.png
  
  # Use named colors
  quick_gradient.py -s darkblue -e lightblue -o ocean.png
  
  # Use a preset
  quick_gradient.py -s navy -e cyan --preset smooth -o smooth_ocean.png
  
  # Custom parameters
  quick_gradient.py -s black -e white --noise 0.005 --waves 5 -o custom.png
  
  # Different sizes
  quick_gradient.py -s red -e yellow --size 1920x1080 -o wallpaper.png
  
  # Batch generation
  quick_gradient.py -s frosty -e midnight --batch 5 --prefix "bg_"

Available presets: %s
Some named colors: %s
        """ % (
            ', '.join(PRESETS.keys()),
            ', '.join(list(NAMED_COLORS.keys())[:10])
        )
    
    parser = argparse.ArgumentParser(
        description='Generate beautiful gradient flow images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog_text
    )
    
    # Required arguments
    parser.add_argument('-s', '--start', required=True, 
                       help='Start color (hex or name)')
    parser.add_argument('-e', '--end', required=True,
                       help='End color (hex or name)')
    
    # Output options
    parser.add_argument('-o', '--output', default='gradient.png',
                       help='Output filename (default: gradient.png)')
    parser.add_argument('--size', default='1080x1920',
                       help='Image size WIDTHxHEIGHT (default: 1080x1920)')
    
    # Direction
    parser.add_argument('-d', '--direction', choices=['vertical', 'horizontal', 'diagonal'],
                       default='vertical', help='Gradient direction')
    
    # Preset or custom parameters
    parser.add_argument('--preset', choices=list(PRESETS.keys()),
                       help='Use a preset configuration')
    parser.add_argument('--noise', type=float, metavar='SCALE',
                       help='Noise scale (0.001-0.01)')
    parser.add_argument('--noise-amp', type=float, metavar='AMP',
                       help='Noise amplitude (0-0.5)')
    parser.add_argument('--waves', type=int, metavar='COUNT',
                       help='Wave count (0-10)')
    parser.add_argument('--wave-amp', type=int, metavar='AMP',
                       help='Wave amplitude (0-200)')
    
    # Batch generation
    parser.add_argument('--batch', type=int, metavar='N',
                       help='Generate N images with variations')
    parser.add_argument('--prefix', default='gradient_',
                       help='Prefix for batch files (default: gradient_)')
    
    # Other options
    parser.add_argument('--show-preview', action='store_true',
                       help='Show preview after generation (requires PIL.show support)')
    parser.add_argument('--list-colors', action='store_true',
                       help='List all available named colors')
    parser.add_argument('--list-presets', action='store_true',
                       help='List all available presets with descriptions')
    
    args = parser.parse_args()
    
    # Handle list commands
    if args.list_colors:
        print("Available named colors:")
        for name, hex_color in sorted(NAMED_COLORS.items()):
            print(f"  {name:15s} {hex_color}")
        return
    
    if args.list_presets:
        print("Available presets:")
        for name, config in PRESETS.items():
            print(f"  {name:12s} - {config['description']}")
            print(f"    Noise: {config['noise_scale']:.3f}, "
                  f"Amplitude: {config['noise_amplitude']:.2f}, "
                  f"Waves: {config['wave_count']}, "
                  f"Wave Amp: {config['wave_amplitude']}")
            print()
        return
    
    # Parse colors
    try:
        start_color = parse_color(args.start)
        end_color = parse_color(args.end)
    except ValueError as e:
        parser.error(str(e))
        return
    
    # Parse size
    try:
        width, height = map(int, args.size.split('x'))
    except:
        parser.error(f"Invalid size format: {args.size}. Use WIDTHxHEIGHT (e.g., 1080x1920)")
        return
    
    # Get parameters
    if args.preset:
        params = PRESETS[args.preset].copy()
        params.pop('description')
        print(f"Using preset: {args.preset}")
    else:
        params = {
            'noise_scale': args.noise or 0.003,
            'noise_amplitude': args.noise_amp or 0.1,
            'wave_count': args.waves if args.waves is not None else 3,
            'wave_amplitude': args.wave_amp or 50
        }
    
    # Override preset with any custom values
    if args.noise:
        params['noise_scale'] = args.noise
    if args.noise_amp:
        params['noise_amplitude'] = args.noise_amp
    if args.waves is not None:
        params['wave_count'] = args.waves
    if args.wave_amp:
        params['wave_amplitude'] = args.wave_amp
    
    # Generate image(s)
    generator = GradientFlowGenerator(width, height)
    
    if args.batch:
        # Batch generation with variations
        print(f"Generating {args.batch} images...")
        for i in range(args.batch):
            # Vary parameters slightly for each image
            variation = 1 + (i - args.batch // 2) * 0.1
            
            img = generator.generate_flow(
                start_color=start_color,
                end_color=end_color,
                flow_direction=args.direction,
                noise_scale=params['noise_scale'] * variation,
                noise_amplitude=params['noise_amplitude'],
                wave_count=params['wave_count'] + (i % 3) - 1,
                wave_amplitude=int(params['wave_amplitude'] * variation)
            )
            
            # Generate filename
            base, ext = os.path.splitext(args.output)
            if args.output == 'gradient.png':
                filename = f"{args.prefix}{i+1:03d}.png"
            else:
                filename = f"{base}_{i+1:03d}{ext}"
            
            img.save(filename)
            print(f"  Saved: {filename}")
    else:
        # Single image generation
        print(f"Generating gradient: {start_color} → {end_color}")
        print(f"Size: {width}x{height}, Direction: {args.direction}")
        print(f"Parameters: noise={params['noise_scale']:.3f}, "
              f"amplitude={params['noise_amplitude']:.2f}, "
              f"waves={params['wave_count']}, "
              f"wave_amp={params['wave_amplitude']}")
        
        img = generator.generate_flow(
            start_color=start_color,
            end_color=end_color,
            flow_direction=args.direction,
            **params
        )
        
        img.save(args.output)
        print(f"Saved: {args.output}")
        
        if args.show_preview:
            try:
                img.show()
            except:
                print("Note: Preview not available on this system")


if __name__ == "__main__":
    main()