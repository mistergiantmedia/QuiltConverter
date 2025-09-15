#!/usr/bin/env python3
"""
Looking Glass Quilt Video Converter - Standalone GUI Application
A user-friendly desktop app for converting quilt videos to Looking Glass ready format

Requirements:
pip install tkinter opencv-python numpy pillow
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
import json
import os
import threading
from pathlib import Path
from PIL import Image, ImageTk
import sys

class QuiltConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Looking Glass Quilt Video Converter")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Variables
        self.quilt_video_path = tk.StringVar()
        self.visual_json_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.conversion_progress = tk.DoubleVar()
        self.is_converting = False
        
        # Create GUI
        self.create_widgets()
        
        # Center window
        self.center_window()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Looking Glass Quilt Video Converter", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Description
        desc_text = ("Convert quilt videos (qs5x9a1.87.mp4) to Looking Glass ready format\n"
                    "using your display's calibration file (visual.json)")
        desc_label = ttk.Label(main_frame, text=desc_text, font=('Arial', 9))
        desc_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        # Input file selection
        row = 2
        ttk.Label(main_frame, text="1. Select Quilt Video:", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=(10, 5))
        
        ttk.Entry(main_frame, textvariable=self.quilt_video_path, width=50).grid(
            row=row+1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(main_frame, text="Browse...", command=self.browse_quilt_video).grid(
            row=row+1, column=2, sticky=tk.W)
        
        # Visual.json file selection
        row += 2
        ttk.Label(main_frame, text="2. Select visual.json:", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=(10, 5))
        
        ttk.Entry(main_frame, textvariable=self.visual_json_path, width=50).grid(
            row=row+1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(main_frame, text="Browse...", command=self.browse_visual_json).grid(
            row=row+1, column=2, sticky=tk.W)
        
        # Output location
        row += 2
        ttk.Label(main_frame, text="3. Choose Output Location:", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=(10, 5))
        
        ttk.Entry(main_frame, textvariable=self.output_path, width=50).grid(
            row=row+1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(main_frame, text="Browse...", command=self.browse_output_location).grid(
            row=row+1, column=2, sticky=tk.W)
        
        # Auto-generate output path checkbox
        row += 2
        self.auto_output = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Auto-generate output filename", 
                       variable=self.auto_output, command=self.update_output_path).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Progress bar
        row += 2
        ttk.Label(main_frame, text="Conversion Progress:", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=(20, 5))
        
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.conversion_progress, 
                                          maximum=100, length=400)
        self.progress_bar.grid(row=row+1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.progress_label = ttk.Label(main_frame, text="Ready to convert", font=('Arial', 9))
        self.progress_label.grid(row=row+2, column=0, columnspan=3)
        
        # Buttons frame
        row += 3
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=row, column=0, columnspan=3, pady=(20, 0))
        
        self.convert_button = ttk.Button(buttons_frame, text="Convert Video", 
                                        command=self.start_conversion, style='Accent.TButton')
        self.convert_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(buttons_frame, text="Help", command=self.show_help).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT)
        
        # Status bar
        row += 1
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W, font=('Arial', 8))
        status_bar.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(20, 0))
    
    def browse_quilt_video(self):
        """Browse for quilt video file"""
        filename = filedialog.askopenfilename(
            title="Select Quilt Video",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if filename:
            self.quilt_video_path.set(filename)
            self.update_output_path()
            self.status_var.set(f"Selected quilt video: {os.path.basename(filename)}")
    
    def browse_visual_json(self):
        """Browse for visual.json file"""
        filename = filedialog.askopenfilename(
            title="Select visual.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.visual_json_path.set(filename)
            self.status_var.set(f"Selected calibration: {os.path.basename(filename)}")
    
    def browse_output_location(self):
        """Browse for output file location"""
        filename = filedialog.asksaveasfilename(
            title="Save Converted Video As",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
            self.auto_output.set(False)
    
    def update_output_path(self):
        """Auto-generate output path based on input video"""
        if self.auto_output.get() and self.quilt_video_path.get():
            input_path = Path(self.quilt_video_path.get())
            output_name = f"{input_path.stem}_LookingGlassReady.mp4"
            output_path = input_path.parent / output_name
            self.output_path.set(str(output_path))
    
    def validate_inputs(self):
        """Validate all input fields"""
        if not self.quilt_video_path.get():
            messagebox.showerror("Error", "Please select a quilt video file")
            return False
        
        if not os.path.exists(self.quilt_video_path.get()):
            messagebox.showerror("Error", "Quilt video file does not exist")
            return False
        
        if not self.visual_json_path.get():
            messagebox.showerror("Error", "Please select a visual.json file")
            return False
        
        if not os.path.exists(self.visual_json_path.get()):
            messagebox.showerror("Error", "visual.json file does not exist")
            return False
        
        if not self.output_path.get():
            messagebox.showerror("Error", "Please specify an output location")
            return False
        
        # Validate JSON file
        try:
            with open(self.visual_json_path.get(), 'r') as f:
                json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Invalid JSON file: {e}")
            return False
        
        return True
    
    def start_conversion(self):
        """Start the video conversion process"""
        if not self.validate_inputs():
            return
        
        if self.is_converting:
            messagebox.showwarning("Warning", "Conversion already in progress")
            return
        
        # Start conversion in separate thread
        self.is_converting = True
        self.convert_button.config(state='disabled', text="Converting...")
        self.conversion_progress.set(0)
        
        thread = threading.Thread(target=self.convert_video, daemon=True)
        thread.start()
    
    def convert_video(self):
        """Convert the quilt video"""
        try:
            converter = QuiltVideoProcessor(
                self.quilt_video_path.get(),
                self.visual_json_path.get(),
                self.output_path.get(),
                progress_callback=self.update_progress
            )
            
            success = converter.process()
            
            # Update UI in main thread
            self.root.after(0, self.conversion_complete, success)
            
        except Exception as e:
            self.root.after(0, self.conversion_error, str(e))
    
    def update_progress(self, progress, message):
        """Update progress bar and message"""
        self.root.after(0, lambda: self.conversion_progress.set(progress))
        self.root.after(0, lambda: self.progress_label.config(text=message))
        self.root.after(0, lambda: self.status_var.set(message))
    
    def conversion_complete(self, success):
        """Handle conversion completion"""
        self.is_converting = False
        self.convert_button.config(state='normal', text="Convert Video")
        
        if success:
            self.progress_label.config(text="Conversion completed successfully!")
            self.status_var.set("Conversion completed successfully!")
            
            result = messagebox.askyesno(
                "Success!", 
                f"Video converted successfully!\n\nOutput: {os.path.basename(self.output_path.get())}\n\n"
                "Would you like to open the output folder?"
            )
            
            if result:
                # Open folder containing output file
                output_dir = os.path.dirname(self.output_path.get())
                if sys.platform == "win32":
                    os.startfile(output_dir)
                elif sys.platform == "darwin":
                    os.system(f"open '{output_dir}'")
                else:
                    os.system(f"xdg-open '{output_dir}'")
        else:
            self.progress_label.config(text="Conversion failed")
            self.status_var.set("Conversion failed")
    
    def conversion_error(self, error_msg):
        """Handle conversion error"""
        self.is_converting = False
        self.convert_button.config(state='normal', text="Convert Video")
        self.progress_label.config(text="Conversion failed")
        self.status_var.set("Conversion failed")
        
        messagebox.showerror("Conversion Error", f"An error occurred during conversion:\n\n{error_msg}")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """Looking Glass Quilt Video Converter Help

This application converts quilt videos to Looking Glass ready format.

Steps:
1. Select your quilt video file (e.g., NameOfVideo_qs5x9a1.87.mp4)
2. Select your Looking Glass calibration file (visual.json)
3. Choose where to save the converted video
4. Click "Convert Video"

The visual.json file contains your Looking Glass display's calibration data and can be found at:
• Windows: %USERPROFILE%\\AppData\\Local\\LookingGlass\\Bridge\\Locations\\LKG-XXXXXX\\LKG_calibration\\visual.json
• macOS: ~/Library/Application Support/LookingGlass/Bridge/Locations/LKG-XXXXXX/LKG_calibration/visual.json
• Linux: ~/.local/share/LookingGlass/Bridge/Locations/LKG-XXXXXX/LKG_calibration/visual.json

The converted video will be ready to play in fullscreen mode on your Looking Glass display.

For support, visit: https://docs.lookingglassfactory.com"""
        
        messagebox.showinfo("Help", help_text)

class QuiltVideoProcessor:
    def __init__(self, quilt_video_path, visual_json_path, output_path, progress_callback=None):
        self.quilt_video_path = quilt_video_path
        self.visual_json_path = visual_json_path
        self.output_path = output_path
        self.progress_callback = progress_callback
        
        # Parse quilt parameters
        self.parse_quilt_filename()
        
        # Load calibration
        self.load_calibration()
    
    def parse_quilt_filename(self):
        """Extract quilt parameters from filename"""
        filename = Path(self.quilt_video_path).stem
        
        # Default values
        self.columns = 5
        self.rows = 9
        self.aspect_ratio = 1.87
        
        # Parse filename (e.g., "qs5x9a1.87")
        if 'qs' in filename:
            parts = filename.split('a')
            if len(parts) >= 2:
                try:
                    self.aspect_ratio = float(parts[1])
                except ValueError:
                    pass
            
            # Extract dimensions
            quilt_part = parts[0].replace('qs', '')
            if 'x' in quilt_part:
                try:
                    cols, rows = quilt_part.split('x')
                    self.columns = int(cols)
                    self.rows = int(rows)
                except ValueError:
                    pass
    
    def load_calibration(self):
        """Load calibration from visual.json"""
        with open(self.visual_json_path, 'r') as f:
            self.calibration = json.load(f)
    
    def update_progress(self, progress, message):
        """Update progress if callback provided"""
        if self.progress_callback:
            self.progress_callback(progress, message)
    
    def process(self):
        """Process the quilt video"""
        self.update_progress(0, "Opening video file...")
        
        # Open input video
        cap = cv2.VideoCapture(self.quilt_video_path)
        if not cap.isOpened():
            raise Exception(f"Cannot open video file: {self.quilt_video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.update_progress(5, f"Video info: {width}x{height}, {fps:.1f} fps, {frame_count} frames")
        
        # Calculate view dimensions
        view_width = width // self.columns
        view_height = height // self.rows
        
        # Setup output video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))
        
        try:
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame with Looking Glass transformation
                processed_frame = self.apply_looking_glass_transform(frame)
                out.write(processed_frame)
                
                frame_idx += 1
                
                # Update progress every 10 frames
                if frame_idx % 10 == 0:
                    progress = 10 + (frame_idx / frame_count) * 85  # 10-95% for processing
                    self.update_progress(progress, f"Processing frame {frame_idx}/{frame_count}")
            
            self.update_progress(95, "Finalizing video...")
            
        finally:
            cap.release()
            out.release()
        
        self.update_progress(100, "Conversion completed!")
        return True
    
    def apply_looking_glass_transform(self, quilt_frame):
        """Apply Looking Glass optical transformation"""
        height, width = quilt_frame.shape[:2]
        
        # Extract calibration parameters
        calibration_data = self.calibration
        center = calibration_data.get('center', {}).get('value', 0.0)
        pitch = calibration_data.get('pitch', {}).get('value', 50.0)
        slope = calibration_data.get('slope', {}).get('value', -5.0)
        dpi = calibration_data.get('DPI', {}).get('value', 338.0)
        
        # Apply lenticular interlacing transformation
        return self.apply_lenticular_interlacing(quilt_frame, center, pitch, slope)
    
    def apply_lenticular_interlacing(self, quilt_frame, center, pitch, slope):
        """Apply lenticular interlacing based on calibration"""
        height, width = quilt_frame.shape[:2]
        output_frame = np.zeros_like(quilt_frame)
        
        view_width = width // self.columns
        view_height = height // self.rows
        total_views = self.columns * self.rows
        
        # For each output pixel column
        for x in range(width):
            # Calculate which view this column should sample from
            # This is a simplified lenticular calculation
            view_offset = ((x - center) / pitch + slope) * total_views
            view_index = int(view_offset) % total_views
            
            # Convert view index to row/column
            view_col = view_index % self.columns
            view_row = view_index // self.columns
            
            # Calculate source position in quilt
            src_x = (view_col * view_width) + (x % view_width)
            src_y_start = view_row * view_height
            
            # Copy the column from the appropriate view
            if src_x < width and src_y_start < height:
                end_y = min(src_y_start + view_height, height)
                output_height = min(height, end_y - src_y_start)
                
                output_frame[:output_height, x] = quilt_frame[src_y_start:src_y_start + output_height, src_x]
        
        return output_frame

def main():
    """Main application entry point"""
    try:
        # Create and run the GUI application
        root = tk.Tk()
        app = QuiltConverterGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Application Error", f"An error occurred: {e}")

if __name__ == "__main__":
    main()
