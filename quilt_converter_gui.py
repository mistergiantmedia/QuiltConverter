#!/usr/bin/env python3
"""
Looking Glass Quilt to Native Video Converter - GUI Version
Simple drag-and-drop interface for converting quilt videos to Looking Glass native format

Requirements: pip install opencv-python numpy tqdm tkinter
"""

import sys
import os
import json
import re
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
from typing import Tuple, Dict, Any

class QuiltConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Looking Glass Quilt Video Converter")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Variables
        self.input_video = tk.StringVar()
        self.visual_json = tk.StringVar()
        self.output_path = tk.StringVar()
        self.calibration = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Looking Glass Quilt Video Converter", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Description
        desc_text = ("Convert quilt videos (e.g., video_qs5x9a1.87.mp4) to Looking Glass native format.\n"
                    "This creates videos that can be displayed directly on your Looking Glass without Bridge.")
        desc_label = ttk.Label(main_frame, text=desc_text, wraplength=550, justify="center")
        desc_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        # Input video selection
        ttk.Label(main_frame, text="1. Select Quilt Video:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.input_video, width=50).grid(row=2, column=1, padx=(10, 5), pady=5, sticky=(tk.W, tk.E))
        ttk.Button(main_frame, text="Browse", command=self.browse_input_video).grid(row=2, column=2, padx=5, pady=5)
        
        # Visual.json selection
        ttk.Label(main_frame, text="2. Select visual.json:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.visual_json, width=50).grid(row=3, column=1, padx=(10, 5), pady=5, sticky=(tk.W, tk.E))
        ttk.Button(main_frame, text="Browse", command=self.browse_visual_json).grid(row=3, column=2, padx=5, pady=5)
        
        # Output path
        ttk.Label(main_frame, text="3. Output Location:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_path, width=50).grid(row=4, column=1, padx=(10, 5), pady=5, sticky=(tk.W, tk.E))
        ttk.Button(main_frame, text="Browse", command=self.browse_output_path).grid(row=4, column=2, padx=5, pady=5)
        
        # Convert button
        self.convert_button = ttk.Button(main_frame, text="Convert Video", 
                                        command=self.start_conversion, style="Accent.TButton")
        self.convert_button.grid(row=5, column=0, columnspan=3, pady=20, ipadx=20, ipady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=6, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to convert")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.grid(row=7, column=0, columnspan=3, pady=5)
        
        # Info text area
        info_frame = ttk.LabelFrame(main_frame, text="Information", padding="10")
        info_frame.grid(row=8, column=0, columnspan=3, pady=20, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.rowconfigure(8, weight=1)
        
        self.info_text = tk.Text(info_frame, height=8, width=70, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        
        self.log_info("Welcome to the Looking Glass Quilt Video Converter!")
        self.log_info("Please select your quilt video file and visual.json calibration file.")
        
    def log_info(self, message):
        """Add a message to the info text area"""
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        self.root.update_idletasks()
        
    def browse_input_video(self):
        """Browse for input quilt video file"""
        filename = filedialog.askopenfilename(
            title="Select Quilt Video File",
            filetypes=[
                ("Video files", "*.mp4 *.mov *.avi *.mkv"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.input_video.set(filename)
            self.auto_set_output_path()
            self.log_info(f"Selected input video: {Path(filename).name}")
            
    def browse_visual_json(self):
        """Browse for visual.json calibration file"""
        filename = filedialog.askopenfilename(
            title="Select visual.json Calibration File",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.visual_json.set(filename)
            self.log_info(f"Selected calibration file: {Path(filename).name}")
            self.load_calibration_info()
            
    def browse_output_path(self):
        """Browse for output video location"""
        filename = filedialog.asksaveasfilename(
            title="Save Converted Video As",
            defaultextension=".mp4",
            filetypes=[
                ("MP4 videos", "*.mp4"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.output_path.set(filename)
            self.log_info(f"Output will be saved to: {Path(filename).name}")
            
    def auto_set_output_path(self):
        """Automatically set output path based on input video"""
        if self.input_video.get():
            input_path = Path(self.input_video.get())
            output_name = f"{input_path.stem}_LookingGlassReady.mp4"
            output_path = input_path.parent / output_name
            self.output_path.set(str(output_path))
            
    def load_calibration_info(self):
        """Load and display calibration information"""
        try:
            with open(self.visual_json.get(), 'r') as f:
                self.calibration = json.load(f)
                
            screen_w = self.calibration.get('screenW', 'Unknown')
            screen_h = self.calibration.get('screenH', 'Unknown')
            pitch = self.calibration.get('pitch', 'Unknown')
            
            self.log_info(f"Calibration loaded: {screen_w}x{screen_h} display, pitch: {pitch}")
            
        except Exception as e:
            self.log_info(f"Error loading calibration: {e}")
            self.calibration = None
            
    def validate_inputs(self):
        """Validate all input parameters"""
        if not self.input_video.get():
            messagebox.showerror("Error", "Please select an input video file.")
            return False
            
        if not os.path.exists(self.input_video.get()):
            messagebox.showerror("Error", "Input video file does not exist.")
            return False
            
        if not self.visual_json.get():
            messagebox.showerror("Error", "Please select a visual.json calibration file.")
            return False
            
        if not os.path.exists(self.visual_json.get()):
            messagebox.showerror("Error", "Visual.json calibration file does not exist.")
            return False
            
        if not self.output_path.get():
            messagebox.showerror("Error", "Please specify an output path.")
            return False
            
        return True
        
    def start_conversion(self):
        """Start the video conversion process in a separate thread"""
        if not self.validate_inputs():
            return
            
        # Disable the convert button
        self.convert_button.config(state="disabled")
        self.progress_var.set(0)
        
        # Start conversion in separate thread
        conversion_thread = threading.Thread(target=self.convert_video)
        conversion_thread.daemon = True
        conversion_thread.start()
        
    def convert_video(self):
        """Convert the quilt video to native format"""
        try:
            self.status_var.set("Loading calibration...")
            
            # Load calibration
            if not self.calibration:
                self.load_calibration_info()
                
            if not self.calibration:
                raise Exception("Could not load calibration data")
            
            # Parse quilt parameters
            filename = Path(self.input_video.get()).name
            quilt_cols, quilt_rows, quilt_aspect = self.parse_quilt_filename(filename)
            
            self.log_info(f"Quilt parameters: {quilt_cols}x{quilt_rows} tiles, aspect {quilt_aspect}")
            
            # Open input video
            self.status_var.set("Opening video...")
            cap = cv2.VideoCapture(self.input_video.get())
            if not cap.isOpened():
                raise Exception(f"Could not open video file")
                
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            self.log_info(f"Input video: {total_frames} frames at {fps:.2f} FPS")
            
            # Setup output video writer
            screen_w = self.calibration.get('screenW', 2560)
            screen_h = self.calibration.get('screenH', 1600)
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(self.output_path.get(), fourcc, fps, (screen_w, screen_h))
            
            if not out.isOpened():
                raise Exception("Could not create output video file")
                
            self.log_info(f"Output resolution: {screen_w}x{screen_h}")
            self.status_var.set("Converting frames...")
            
            # Process each frame
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Convert frame
                native_frame = self.create_native_frame(frame, quilt_cols, quilt_rows, quilt_aspect)
                out.write(native_frame)
                
                # Update progress
                frame_count += 1
                progress = (frame_count / total_frames) * 100
                self.progress_var.set(progress)
                
                if frame_count % 30 == 0:  # Update status every 30 frames
                    self.status_var.set(f"Converting frames... {frame_count}/{total_frames}")
                    
            # Cleanup
            cap.release()
            out.release()
            
            self.status_var.set("Conversion complete!")
            self.progress_var.set(100)
            self.log_info("✓ Conversion successful!")
            self.log_info(f"Output saved to: {Path(self.output_path.get()).name}")
            
            messagebox.showinfo("Success", "Video conversion completed successfully!")
            
        except Exception as e:
            self.log_info(f"Error during conversion: {e}")
            self.status_var.set(f"Error: {e}")
            messagebox.showerror("Conversion Error", f"An error occurred during conversion:\n{e}")
            
        finally:
            # Re-enable the convert button
            self.convert_button.config(state="normal")
            
    def parse_quilt_filename(self, filename: str) -> Tuple[int, int, float]:
        """Parse quilt parameters from filename"""
        pattern = r'qs(\d+)x(\d+)a([\d.]+)'
        match = re.search(pattern, filename)
        
        if not match:
            self.log_info("Warning: Could not parse quilt parameters. Using defaults: 5x9, aspect 1.87")
            return 5, 9, 1.87
            
        cols = int(match.group(1))
        rows = int(match.group(2))
        aspect = float(match.group(3))
        
        return cols, rows, aspect
        
    def create_native_frame(self, quilt_frame: np.ndarray, quilt_cols: int, quilt_rows: int, quilt_aspect: float) -> np.ndarray:
        """Convert a single quilt frame to native Looking Glass format"""
        quilt_h, quilt_w = quilt_frame.shape[:2]
        
        # Calculate tile dimensions
        tile_w = quilt_w // quilt_cols
        tile_h = quilt_h // quilt_rows
        
        # Create output native image
        native_w = self.calibration.get('screenW', 2560)
        native_h = self.calibration.get('screenH', 1600)
        native_frame = np.zeros((native_h, native_w, 3), dtype=np.uint8)
        
        # Extract calibration parameters
        center = self.calibration.get('center', 0.0)
        pitch = self.calibration.get('pitch', 49.825)
        slope = self.calibration.get('slope', -5.2094)
        
        # Convert each pixel in the native image
        for y in range(native_h):
            for x in range(native_w):
                # Normalize coordinates to [-1, 1]
                norm_x = (2.0 * x / native_w) - 1.0
                norm_y = (2.0 * y / native_h) - 1.0
                
                # Calculate which view this pixel should sample from
                view_angle = norm_x * slope + center
                view_index = (view_angle + 1.0) * 0.5 * (quilt_cols * quilt_rows - 1)
                view_index = max(0, min(quilt_cols * quilt_rows - 1, int(view_index)))
                
                # Convert view index to tile coordinates
                tile_y = view_index // quilt_cols
                tile_x = view_index % quilt_cols
                
                # Calculate pixel position within the tile
                tile_pixel_x = int((norm_x + 1.0) * 0.5 * tile_w)
                tile_pixel_y = int((norm_y + 1.0) * 0.5 * tile_h)
                
                # Clamp to tile boundaries
                tile_pixel_x = max(0, min(tile_w - 1, tile_pixel_x))
                tile_pixel_y = max(0, min(tile_h - 1, tile_pixel_y))
                
                # Calculate absolute coordinates in quilt
                quilt_x = tile_x * tile_w + tile_pixel_x
                quilt_y = tile_y * tile_h + tile_pixel_y
                
                # Sample from quilt and assign to native frame
                native_frame[y, x] = quilt_frame[quilt_y, quilt_x]
                
        return native_frame

def main():
    # Check for required modules
    try:
        import cv2
        import numpy as np
        import tkinter as tk
    except ImportError as e:
        print(f"Required module not found: {e}")
        print("Please install required packages: pip install opencv-python numpy")
        sys.exit(1)
        
    root = tk.Tk()
    app = QuiltConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()