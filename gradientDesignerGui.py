#!/usr/bin/env python3
"""
Interactive Gradient Flow Designer
GUI application for creating and previewing gradient flows with real-time adjustments
"""

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from PIL import Image, ImageTk
import json
from gradientFlowGenerator import GradientFlowGenerator
import threading

class GradientFlowDesigner:
    """Interactive GUI for designing gradient flows"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Gradient Flow Designer")
        self.root.geometry("1400x900")
        
        # Initialize generator
        self.generator = GradientFlowGenerator(540, 960)  # Half resolution for preview
        
        # Current settings
        self.start_color = '#1a3a52'
        self.end_color = '#8cc8d8'
        self.current_image = None
        self.preview_image = None
        
        # Setup UI
        self.setup_ui()
        
        # Generate initial preview
        self.generate_preview()
    
    def setup_ui(self):
        """Create the user interface"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Left panel - Controls
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        row = 0
        
        # Color selection
        ttk.Label(control_frame, text="Colors", font=('Arial', 12, 'bold')).grid(row=row, column=0, columnspan=3, pady=(0, 10))
        row += 1
        
        ttk.Label(control_frame, text="Start Color:").grid(row=row, column=0, sticky=tk.W)
        self.start_color_label = tk.Label(control_frame, width=20, height=1, bg=self.start_color)
        self.start_color_label.grid(row=row, column=1, padx=5)
        ttk.Button(control_frame, text="Choose", command=lambda: self.choose_color('start')).grid(row=row, column=2)
        row += 1
        
        ttk.Label(control_frame, text="End Color:").grid(row=row, column=0, sticky=tk.W)
        self.end_color_label = tk.Label(control_frame, width=20, height=1, bg=self.end_color)
        self.end_color_label.grid(row=row, column=1, padx=5)
        ttk.Button(control_frame, text="Choose", command=lambda: self.choose_color('end')).grid(row=row, column=2)
        row += 1
        
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Flow parameters
        ttk.Label(control_frame, text="Flow Parameters", font=('Arial', 12, 'bold')).grid(row=row, column=0, columnspan=3, pady=(0, 10))
        row += 1
        
        # Direction
        ttk.Label(control_frame, text="Direction:").grid(row=row, column=0, sticky=tk.W)
        self.direction_var = tk.StringVar(value="vertical")
        direction_combo = ttk.Combobox(control_frame, textvariable=self.direction_var, 
                                      values=["vertical", "horizontal", "diagonal"], 
                                      state="readonly", width=18)
        direction_combo.grid(row=row, column=1, columnspan=2, padx=5)
        direction_combo.bind('<<ComboboxSelected>>', lambda e: self.on_parameter_change())
        row += 1
        
        # Noise Scale
        ttk.Label(control_frame, text="Noise Scale:").grid(row=row, column=0, sticky=tk.W)
        self.noise_scale_var = tk.DoubleVar(value=0.003)
        self.noise_scale_slider = ttk.Scale(control_frame, from_=0.001, to=0.01, 
                                           variable=self.noise_scale_var, 
                                           orient=tk.HORIZONTAL, length=200,
                                           command=lambda v: self.update_scale_label('noise_scale'))
        self.noise_scale_slider.grid(row=row, column=1, padx=5)
        self.noise_scale_label = ttk.Label(control_frame, text="0.003")
        self.noise_scale_label.grid(row=row, column=2)
        row += 1
        
        # Noise Amplitude
        ttk.Label(control_frame, text="Noise Amplitude:").grid(row=row, column=0, sticky=tk.W)
        self.noise_amp_var = tk.DoubleVar(value=0.15)
        self.noise_amp_slider = ttk.Scale(control_frame, from_=0.0, to=0.5, 
                                         variable=self.noise_amp_var, 
                                         orient=tk.HORIZONTAL, length=200,
                                         command=lambda v: self.update_scale_label('noise_amp'))
        self.noise_amp_slider.grid(row=row, column=1, padx=5)
        self.noise_amp_label = ttk.Label(control_frame, text="0.15")
        self.noise_amp_label.grid(row=row, column=2)
        row += 1
        
        # Wave Count
        ttk.Label(control_frame, text="Wave Count:").grid(row=row, column=0, sticky=tk.W)
        self.wave_count_var = tk.IntVar(value=3)
        self.wave_count_slider = ttk.Scale(control_frame, from_=0, to=10, 
                                          variable=self.wave_count_var, 
                                          orient=tk.HORIZONTAL, length=200,
                                          command=lambda v: self.update_scale_label('wave_count'))
        self.wave_count_slider.grid(row=row, column=1, padx=5)
        self.wave_count_label = ttk.Label(control_frame, text="3")
        self.wave_count_label.grid(row=row, column=2)
        row += 1
        
        # Wave Amplitude
        ttk.Label(control_frame, text="Wave Amplitude:").grid(row=row, column=0, sticky=tk.W)
        self.wave_amp_var = tk.IntVar(value=50)
        self.wave_amp_slider = ttk.Scale(control_frame, from_=0, to=200, 
                                        variable=self.wave_amp_var, 
                                        orient=tk.HORIZONTAL, length=200,
                                        command=lambda v: self.update_scale_label('wave_amp'))
        self.wave_amp_slider.grid(row=row, column=1, padx=5)
        self.wave_amp_label = ttk.Label(control_frame, text="50")
        self.wave_amp_label.grid(row=row, column=2)
        row += 1
        
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Preset buttons
        ttk.Label(control_frame, text="Presets", font=('Arial', 12, 'bold')).grid(row=row, column=0, columnspan=3, pady=(0, 10))
        row += 1
        
        preset_frame = ttk.Frame(control_frame)
        preset_frame.grid(row=row, column=0, columnspan=3)
        
        ttk.Button(preset_frame, text="Smooth Flow", command=lambda: self.apply_preset('smooth')).grid(row=0, column=0, padx=2)
        ttk.Button(preset_frame, text="Wavy", command=lambda: self.apply_preset('wavy')).grid(row=0, column=1, padx=2)
        ttk.Button(preset_frame, text="Turbulent", command=lambda: self.apply_preset('turbulent')).grid(row=0, column=2, padx=2)
        row += 1
        
        ttk.Button(preset_frame, text="Minimal", command=lambda: self.apply_preset('minimal')).grid(row=1, column=0, padx=2, pady=5)
        ttk.Button(preset_frame, text="Dramatic", command=lambda: self.apply_preset('dramatic')).grid(row=1, column=1, padx=2, pady=5)
        ttk.Button(preset_frame, text="Subtle", command=lambda: self.apply_preset('subtle')).grid(row=1, column=2, padx=2, pady=5)
        row += 1
        
        ttk.Separator(control_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Action buttons
        ttk.Label(control_frame, text="Actions", font=('Arial', 12, 'bold')).grid(row=row, column=0, columnspan=3, pady=(0, 10))
        row += 1
        
        self.generate_button = ttk.Button(control_frame, text="Generate Preview", 
                                         command=self.generate_preview)
        self.generate_button.grid(row=row, column=0, columnspan=3, pady=5)
        row += 1
        
        self.save_button = ttk.Button(control_frame, text="Save Full Resolution", 
                                     command=self.save_full_resolution)
        self.save_button.grid(row=row, column=0, columnspan=3, pady=5)
        row += 1
        
        self.batch_button = ttk.Button(control_frame, text="Generate Batch", 
                                      command=self.generate_batch)
        self.batch_button.grid(row=row, column=0, columnspan=3, pady=5)
        row += 1
        
        self.export_button = ttk.Button(control_frame, text="Export Settings", 
                                       command=self.export_settings)
        self.export_button.grid(row=row, column=0, columnspan=3, pady=5)
        row += 1
        
        self.import_button = ttk.Button(control_frame, text="Import Settings", 
                                       command=self.import_settings)
        self.import_button.grid(row=row, column=0, columnspan=3, pady=5)
        
        # Right panel - Preview
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="10")
        preview_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Canvas for preview
        self.canvas = tk.Canvas(preview_frame, width=540, height=960, bg='gray20')
        self.canvas.grid(row=0, column=0)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def update_scale_label(self, param_name):
        """Update the label next to sliders"""
        if param_name == 'noise_scale':
            self.noise_scale_label.config(text=f"{self.noise_scale_var.get():.3f}")
        elif param_name == 'noise_amp':
            self.noise_amp_label.config(text=f"{self.noise_amp_var.get():.2f}")
        elif param_name == 'wave_count':
            self.wave_count_label.config(text=f"{int(self.wave_count_var.get())}")
        elif param_name == 'wave_amp':
            self.wave_amp_label.config(text=f"{int(self.wave_amp_var.get())}")
        
        self.on_parameter_change()
    
    def on_parameter_change(self):
        """Called when any parameter changes"""
        # Auto-generate preview on parameter change (optional)
        # self.generate_preview()
        pass
    
    def choose_color(self, color_type):
        """Open color chooser dialog"""
        color = colorchooser.askcolor(initialcolor=self.start_color if color_type == 'start' else self.end_color)
        if color[1]:
            if color_type == 'start':
                self.start_color = color[1]
                self.start_color_label.config(bg=self.start_color)
            else:
                self.end_color = color[1]
                self.end_color_label.config(bg=self.end_color)
            self.generate_preview()
    
    def apply_preset(self, preset_name):
        """Apply predefined parameter presets"""
        presets = {
            'smooth': {
                'noise_scale': 0.002,
                'noise_amp': 0.05,
                'wave_count': 2,
                'wave_amp': 30,
                'direction': 'vertical'
            },
            'wavy': {
                'noise_scale': 0.003,
                'noise_amp': 0.1,
                'wave_count': 5,
                'wave_amp': 80,
                'direction': 'vertical'
            },
            'turbulent': {
                'noise_scale': 0.008,
                'noise_amp': 0.3,
                'wave_count': 7,
                'wave_amp': 120,
                'direction': 'diagonal'
            },
            'minimal': {
                'noise_scale': 0.001,
                'noise_amp': 0.02,
                'wave_count': 1,
                'wave_amp': 20,
                'direction': 'vertical'
            },
            'dramatic': {
                'noise_scale': 0.005,
                'noise_amp': 0.25,
                'wave_count': 4,
                'wave_amp': 100,
                'direction': 'diagonal'
            },
            'subtle': {
                'noise_scale': 0.002,
                'noise_amp': 0.08,
                'wave_count': 3,
                'wave_amp': 40,
                'direction': 'vertical'
            }
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            self.noise_scale_var.set(preset['noise_scale'])
            self.noise_amp_var.set(preset['noise_amp'])
            self.wave_count_var.set(preset['wave_count'])
            self.wave_amp_var.set(preset['wave_amp'])
            self.direction_var.set(preset['direction'])
            
            # Update labels
            self.update_scale_label('noise_scale')
            self.update_scale_label('noise_amp')
            self.update_scale_label('wave_count')
            self.update_scale_label('wave_amp')
            
            self.generate_preview()
            self.status_var.set(f"Applied preset: {preset_name}")
    
    def generate_preview(self):
        """Generate and display preview image"""
        self.status_var.set("Generating preview...")
        self.generate_button.config(state='disabled')
        
        def generate():
            try:
                self.current_image = self.generator.generate_flow(
                    start_color=self.start_color,
                    end_color=self.end_color,
                    flow_direction=self.direction_var.get(),
                    noise_scale=self.noise_scale_var.get(),
                    noise_amplitude=self.noise_amp_var.get(),
                    wave_count=int(self.wave_count_var.get()),
                    wave_amplitude=int(self.wave_amp_var.get())
                )
                
                # Convert for display
                self.preview_image = ImageTk.PhotoImage(self.current_image)
                
                # Update canvas
                self.canvas.delete("all")
                self.canvas.create_image(270, 480, image=self.preview_image)
                
                self.status_var.set("Preview generated")
                self.generate_button.config(state='normal')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate preview: {str(e)}")
                self.status_var.set("Error generating preview")
                self.generate_button.config(state='normal')
        
        # Run in thread to keep UI responsive
        thread = threading.Thread(target=generate)
        thread.start()
    
    def save_full_resolution(self):
        """Save the current design at full resolution"""
        if not self.current_image:
            messagebox.showwarning("Warning", "Please generate a preview first")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filename:
            self.status_var.set("Generating full resolution...")
            
            # Generate at full resolution
            full_generator = GradientFlowGenerator(1080, 1920)
            full_image = full_generator.generate_flow(
                start_color=self.start_color,
                end_color=self.end_color,
                flow_direction=self.direction_var.get(),
                noise_scale=self.noise_scale_var.get(),
                noise_amplitude=self.noise_amp_var.get(),
                wave_count=int(self.wave_count_var.get()),
                wave_amplitude=int(self.wave_amp_var.get())
            )
            
            full_image.save(filename)
            self.status_var.set(f"Saved: {filename}")
            messagebox.showinfo("Success", f"Image saved to {filename}")
    
    def generate_batch(self):
        """Generate a batch of stackable images"""
        dialog = BatchGeneratorDialog(self.root, self)
        self.root.wait_window(dialog.top)
    
    def export_settings(self):
        """Export current settings to JSON file"""
        settings = {
            'start_color': self.start_color,
            'end_color': self.end_color,
            'direction': self.direction_var.get(),
            'noise_scale': self.noise_scale_var.get(),
            'noise_amplitude': self.noise_amp_var.get(),
            'wave_count': int(self.wave_count_var.get()),
            'wave_amplitude': int(self.wave_amp_var.get())
        }
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            with open(filename, 'w') as f:
                json.dump(settings, f, indent=2)
            self.status_var.set(f"Settings exported to {filename}")
    
    def import_settings(self):
        """Import settings from JSON file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    settings = json.load(f)
                
                self.start_color = settings['start_color']
                self.end_color = settings['end_color']
                self.start_color_label.config(bg=self.start_color)
                self.end_color_label.config(bg=self.end_color)
                
                self.direction_var.set(settings['direction'])
                self.noise_scale_var.set(settings['noise_scale'])
                self.noise_amp_var.set(settings['noise_amplitude'])
                self.wave_count_var.set(settings['wave_count'])
                self.wave_amp_var.set(settings['wave_amplitude'])
                
                # Update labels
                self.update_scale_label('noise_scale')
                self.update_scale_label('noise_amp')
                self.update_scale_label('wave_count')
                self.update_scale_label('wave_amp')
                
                self.generate_preview()
                self.status_var.set(f"Settings imported from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import settings: {str(e)}")


class BatchGeneratorDialog:
    """Dialog for batch generation settings"""
    
    def __init__(self, parent, main_app):
        self.main_app = main_app
        self.top = tk.Toplevel(parent)
        self.top.title("Batch Generator")
        self.top.geometry("400x350")
        
        # Colors list
        ttk.Label(self.top, text="Colors (hex, one per line):").pack(pady=10)
        
        self.colors_text = tk.Text(self.top, height=6, width=40)
        self.colors_text.pack(pady=5)
        
        # Default colors
        default_colors = "#1a3a52\n#2d5873\n#4a7c94\n#6ba3b5\n#8cc8d8\n#3d6b7d"
        self.colors_text.insert('1.0', default_colors)
        
        # Image count
        frame = ttk.Frame(self.top)
        frame.pack(pady=10)
        ttk.Label(frame, text="Number of images:").pack(side=tk.LEFT)
        self.count_var = tk.IntVar(value=6)
        ttk.Spinbox(frame, from_=1, to=20, textvariable=self.count_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Output directory
        self.output_dir = tk.StringVar(value="./gradient_batch")
        dir_frame = ttk.Frame(self.top)
        dir_frame.pack(pady=10)
        ttk.Label(dir_frame, text="Output directory:").pack()
        ttk.Entry(dir_frame, textvariable=self.output_dir, width=35).pack(side=tk.LEFT)
        ttk.Button(dir_frame, text="Browse", command=self.choose_directory).pack(side=tk.LEFT, padx=5)
        
        # Generate button
        ttk.Button(self.top, text="Generate Batch", command=self.generate).pack(pady=20)
    
    def choose_directory(self):
        """Choose output directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)
    
    def generate(self):
        """Generate batch of images"""
        colors = [line.strip() for line in self.colors_text.get('1.0', tk.END).split('\n') if line.strip()]
        
        if not colors:
            messagebox.showerror("Error", "Please provide at least one color")
            return
        
        import os
        output_dir = self.output_dir.get()
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate images
        from gradientFlowGenerator import create_stackable_sequence
        
        try:
            images = create_stackable_sequence(
                colors=colors,
                image_count=self.count_var.get(),
                output_prefix=os.path.join(output_dir, "flow")
            )
            
            messagebox.showinfo("Success", f"Generated {len(images)} images in {output_dir}")
            self.top.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate batch: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = GradientFlowDesigner(root)
    root.mainloop()