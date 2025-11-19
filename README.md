# Gradient Flow Generator

A comprehensive Python toolkit for creating beautiful, flowing gradient images with Perlin noise effects. Perfect for creating wallpapers, backgrounds, and artistic stackable image sequences.

## Features

- 🎨 **Smooth Gradient Flows**: Create flowing gradients with customizable colors and transitions
- 🌊 **Perlin Noise Integration**: Add organic, natural-looking variations to gradients
- 🔄 **Stackable Sequences**: Generate series of images that flow seamlessly together
- 🖼️ **Interactive GUI**: Real-time preview and parameter adjustment
- ⚡ **Batch Processing**: Generate multiple variations automatically
- 🎯 **Presets**: Quick access to popular gradient styles

## Installation

### Requirements

```bash
pip install pillow numpy
```

For the GUI interface (optional):
```bash
pip install tkinter  # Usually comes with Python
```

## Files Overview

1. **`gradient_flow_generator.py`** - Core generator library
2. **`gradient_designer_gui.py`** - Interactive GUI application
3. **`batch_gradient_processor.py`** - Batch processing tool
4. **`quick_gradient.py`** - Simple CLI for quick generation

## Quick Start

### 1. Simple Command Line Usage

```bash
# Generate a simple gradient
python quick_gradient.py -s "#1a3a52" -e "#8cc8d8" -o my_gradient.png

# Use named colors
python quick_gradient.py -s darkblue -e lightblue -o ocean.png

# Apply a preset
python quick_gradient.py -s navy -e cyan --preset smooth -o smooth_ocean.png

# Generate multiple variations
python quick_gradient.py -s frosty -e midnight --batch 5 --prefix "bg_"
```

### 2. Interactive GUI

```bash
python gradient_designer_gui.py
```

Features:
- Real-time preview
- Color picker
- Parameter sliders
- Preset buttons
- Export/Import settings
- Batch generation

### 3. Python API Usage

```python
from gradient_flow_generator import GradientFlowGenerator

# Create generator
generator = GradientFlowGenerator(width=1080, height=1920)

# Generate a gradient
image = generator.generate_flow(
    start_color='#1a3a52',
    end_color='#8cc8d8',
    flow_direction='vertical',
    noise_scale=0.003,
    noise_amplitude=0.15,
    wave_count=3,
    wave_amplitude=50
)

# Save the image
image.save('gradient.png')
```

## Color Schemes

### Frosty (Your Colors)
```python
frosty_colors = [
    '#1a3a52',  # Deep blue
    '#2d5873',  # Medium blue
    '#4a7c94',  # Light blue
    '#6ba3b5',  # Cyan blue
    '#8cc8d8',  # Light cyan
    '#3d6b7d',  # Teal
]
```

### Other Presets
- **Sunset**: Warm gradients from dark purple to pink
- **Ocean**: Deep sea blues to light cyan
- **Forest**: Natural greens
- **Monochrome**: Grayscale variations

## Parameters Explained

### Noise Scale (0.001 - 0.01)
- **Lower values** (0.001-0.003): Smoother, larger patterns
- **Higher values** (0.005-0.01): More detailed, turbulent patterns

### Noise Amplitude (0.0 - 0.5)
- **Lower values** (0.0-0.1): Subtle variations
- **Higher values** (0.2-0.5): Strong distortions

### Wave Count (0 - 10)
- Number of wave undulations in the gradient
- 0 = no waves, straight gradient
- 3-5 = gentle waves
- 7-10 = complex wave patterns

### Wave Amplitude (0 - 200)
- Strength of wave effect in pixels
- 20-50 = subtle waves
- 50-100 = moderate waves
- 100-200 = dramatic waves

## Presets

### Smooth
```python
noise_scale=0.002, noise_amplitude=0.05, wave_count=2, wave_amplitude=30
```
Perfect for subtle, professional backgrounds

### Wavy
```python
noise_scale=0.003, noise_amplitude=0.1, wave_count=5, wave_amplitude=80
```
Dynamic flowing patterns

### Turbulent
```python
noise_scale=0.008, noise_amplitude=0.3, wave_count=7, wave_amplitude=120
```
Dramatic, energetic flows

### Minimal
```python
noise_scale=0.001, noise_amplitude=0.02, wave_count=1, wave_amplitude=20
```
Clean, simple gradients

### Dunes
```python
noise_scale=0.004, noise_amplitude=0.15, wave_count=4, wave_amplitude=60
```
Sand dune-like patterns (similar to your reference images)

## Batch Processing

### Create Stackable Sequences

```bash
python batch_gradient_processor.py --scheme frosty --count 6
```

### Process All Color Schemes

```bash
python batch_gradient_processor.py
```

This will generate:
- Multiple sequences for each color scheme
- Preview grids for easy viewing
- Organized output directories

### Custom Configuration

Create a configuration file:
```bash
python batch_gradient_processor.py --create-config
```

Edit `gradient_config.json` to customize:
- Color schemes
- Sequence parameters
- Output settings

## Creating Stackable Flows

For images that stack seamlessly:

```python
from gradient_flow_generator import create_stackable_sequence

# Create a sequence that flows from dark to light and back
sequence = create_stackable_sequence(
    colors=['#1a3a52', '#4a7c94', '#8cc8d8'],
    image_count=6,
    output_prefix='stackable'
)
```

This ensures:
- Smooth color transitions between images
- Alternating dark-to-light patterns
- Consistent flow direction

## Advanced Usage

### Multi-Layer Flows

```python
generator = GradientFlowGenerator()

# Create complex multi-layer gradient
image = generator.generate_multi_layer_flow(
    colors=['#1a3a52', '#4a7c94', '#8cc8d8'],
    layer_count=3,
    opacity_range=(0.3, 0.7)
)
```

### Custom Gradient Stops

```python
# Multi-stop gradient with specific positions
image = generator.generate_flow(
    start_color='#1a3a52',
    end_color='#8cc8d8',
    gradient_stops=[0.0, 0.3, 0.7, 1.0]  # Color positions
)
```

## Tips for Best Results

1. **For Wallpapers**: Use vertical direction with smooth preset
2. **For Artistic Effects**: Combine high wave count with moderate noise
3. **For Seamless Loops**: Use transition pairs or stackable sequences
4. **For Subtle Backgrounds**: Keep noise amplitude below 0.1
5. **For Dynamic Flows**: Use diagonal direction with turbulent preset

## Examples

### Example 1: Frosty Wallpaper
```bash
python quick_gradient.py -s "#1a3a52" -e "#8cc8d8" \
    --preset smooth --size 1920x1080 -o frosty_wallpaper.png
```

### Example 2: Instagram Story Sequence
```bash
python batch_gradient_processor.py \
    --colors "#1a3a52" "#6ba3b5" "#8cc8d8" \
    --count 5 --output instagram_stories
```

### Example 3: Dynamic Background
```bash
python quick_gradient.py -s midnight -e cyan \
    --preset turbulent -d diagonal -o dynamic_bg.png
```

## Troubleshooting

### Issue: Images look too noisy
- Reduce `noise_amplitude` to 0.05 or lower
- Decrease `noise_scale` to 0.002 or lower

### Issue: Gradients look flat
- Increase `wave_count` to 3-5
- Add more `noise_amplitude` (0.1-0.2)

### Issue: Colors don't blend well
- The generator uses HSV color space for smooth transitions
- Try colors that are closer in hue
- Use the multi-layer approach for complex blends

## License

MIT License - Feel free to use in your projects!

## Contributing

Feel free to submit issues, fork, and create pull requests!

## Acknowledgments

Inspired by the beautiful flowing gradients often seen in modern UI design and abstract art.