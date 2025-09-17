#!/usr/bin/env python3
"""
Looking Glass Quilt Video Converter
Converts quilt videos to Looking Glass display-ready format using calibration data.
"""

import os
import sys
import json
import math
import tempfile
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import cv2
import numpy as np
from PIL import Image

class QuiltConverter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Looking Glass Quilt Video Converter")
        self.root.geometry("800x600")
        
        # Queue for thread communication
        self.message_queue = queue.Queue()
        
        # Variables
        self.quilt_file = tk.StringVar()
        self.calibration_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.output_codec = tk.StringVar(value="H.264")
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready")
        
        self.setup_ui()
        self.check_queue()
        
    def setup_ui(self):
        """Set up the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Looking Glass Quilt Video Converter", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Quilt video file selection
        ttk.Label(main_frame, text="Quilt Video File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.quilt_file, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_quilt_file).grid(row=1, column=2, padx=(5, 0))
        
        # Calibration file selection
        ttk.Label(main_frame, text="Calibration File (visual.json):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.calibration_file, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_calibration_file).grid(row=2, column=2, padx=(5, 0))
        
        # Output file selection
        ttk.Label(main_frame, text="Output File:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_file, width=50).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output_file).grid(row=3, column=2, padx=(5, 0))
        
        # Output codec selection
        ttk.Label(main_frame, text="Output Codec:").grid(row=4, column=0, sticky=tk.W, pady=5)
        codec_frame = ttk.Frame(main_frame)
        codec_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5)
        
        codec_combo = ttk.Combobox(codec_frame, textvariable=self.output_codec, width=25, state="readonly")
        codec_combo['values'] = ("H.264", "H.265 (HEVC)", "ProRes 422", "H.264 YUV 4:4:4", "H.265 YUV 4:4:4", "ProRes 4444")
        codec_combo.grid(row=0, column=0, sticky=tk.W)
        
        # Codec info label
        self.codec_info = ttk.Label(codec_frame, text="", foreground="gray", font=("Arial", 8))
        self.codec_info.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Bind codec selection to update info
        codec_combo.bind('<<ComboboxSelected>>', self.update_codec_info)
        self.update_codec_info()  # Initialize with default
        
        # Convert button
        convert_btn = ttk.Button(main_frame, text="Convert Video", command=self.start_conversion)
        convert_btn.grid(row=5, column=0, columnspan=3, pady=20)
        
        # Progress bar
        ttk.Label(main_frame, text="Progress:").grid(row=6, column=0, sticky=tk.W, pady=5)
        progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        progress_bar.grid(row=6, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Status label
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=7, column=0, columnspan=3, pady=5)
        
        # Log output
        ttk.Label(main_frame, text="Log Output:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.log_text = scrolledtext.ScrolledText(main_frame, width=80, height=15)
        self.log_text.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(9, weight=1)
        
    def update_codec_info(self, event=None):
        """Update codec information display"""
        codec = self.output_codec.get()
        info_text = ""
        
        if codec == "H.264":
            info_text = "Good compatibility, moderate file size (YUV 4:2:0)"
        elif codec == "H.265 (HEVC)":
            info_text = "Better compression, may need newer devices (YUV 4:2:0)"
        elif codec == "ProRes 422":
            info_text = "High quality, large file size, best for editing (YUV 4:2:2)"
        elif codec == "H.264 YUV 4:4:4":
            info_text = "Full chroma resolution, ideal for Looking Glass (YUV 4:4:4)"
        elif codec == "H.265 YUV 4:4:4":
            info_text = "Best compression + full chroma (YUV 4:4:4)"
        elif codec == "ProRes 4444":
            info_text = "Highest quality with alpha support (YUV 4:4:4:4)"
            
        self.codec_info.config(text=info_text)
        
        # Update file extension in output filename if set
        if self.output_file.get():
            current_path = Path(self.output_file.get())
            if codec in ["ProRes 422", "ProRes 4444"]:
                new_extension = ".mov"
            else:
                new_extension = ".mp4"
            
            new_path = current_path.with_suffix(new_extension)
            self.output_file.set(str(new_path))
            
    def browse_quilt_file(self):
        filename = filedialog.askopenfilename(
            title="Select Quilt Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.quilt_file.set(filename)
            # Auto-generate output filename
            base_name = Path(filename).stem
            if "_qs" in base_name:
                base_name = base_name.split("_qs")[0]
            
            # Choose extension based on codec
            codec = self.output_codec.get()
            extension = ".mov" if codec in ["ProRes 422", "ProRes 4444"] else ".mp4"
            output_name = f"{base_name}_LookingGlassReady{extension}"
            output_path = Path(filename).parent / output_name
            self.output_file.set(str(output_path))
            
    def browse_calibration_file(self):
        filename = filedialog.askopenfilename(
            title="Select Calibration File (visual.json)",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.calibration_file.set(filename)
            
    def browse_output_file(self):
        codec = self.output_codec.get()
        if codec in ["ProRes 422", "ProRes 4444"]:
            filetypes = [("MOV files", "*.mov"), ("All files", "*.*")]
            defaultextension = ".mov"
        else:
            filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
            defaultextension = ".mp4"
            
        filename = filedialog.asksaveasfilename(
            title="Save Output Video As",
            defaultextension=defaultextension,
            filetypes=filetypes
        )
        if filename:
            self.output_file.set(filename)
            
    def log_message(self, message):
        """Add a message to the log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def check_queue(self):
        """Check for messages from worker thread"""
        try:
            while True:
                message_type, data = self.message_queue.get_nowait()
                if message_type == "log":
                    self.log_message(data)
                elif message_type == "progress":
                    self.progress_var.set(data)
                elif message_type == "status":
                    self.status_var.set(data)
                elif message_type == "done":
                    self.conversion_complete(data)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)
            
    def start_conversion(self):
        """Start the conversion process in a separate thread"""
        if not self.validate_inputs():
            return
            
        # Clear log
        self.log_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.status_var.set("Converting...")
        
        # Start conversion thread
        thread = threading.Thread(target=self.convert_video, daemon=True)
        thread.start()
        
    def validate_inputs(self):
        """Validate user inputs"""
        if not self.quilt_file.get():
            messagebox.showerror("Error", "Please select a quilt video file")
            return False
            
        if not os.path.exists(self.quilt_file.get()):
            messagebox.showerror("Error", "Quilt video file does not exist")
            return False
            
        if not self.calibration_file.get():
            messagebox.showerror("Error", "Please select a calibration file")
            return False
            
        if not os.path.exists(self.calibration_file.get()):
            messagebox.showerror("Error", "Calibration file does not exist")
            return False
            
        if not self.output_file.get():
            messagebox.showerror("Error", "Please specify an output file")
            return False
            
        return True
        
    def parse_quilt_filename(self, filename):
        """Parse quilt parameters from filename"""
        basename = Path(filename).stem
        
        # Look for pattern like _qs5x9a1.87
        import re
        pattern = r'_qs(\d+)x(\d+)a([\d.]+)'
        match = re.search(pattern, basename)
        
        if match:
            cols = int(match.group(1))
            rows = int(match.group(2))
            aspect = float(match.group(3))
            return cols, rows, aspect
        else:
            # Default values if pattern not found
            self.message_queue.put(("log", "Warning: Could not parse quilt parameters from filename, using defaults (5x9, aspect 1.87)"))
            return 5, 9, 1.87
            
    def load_calibration(self, calib_file):
        """Load calibration data from visual.json"""
        try:
            with open(calib_file, 'r') as f:
                calib = json.load(f)
            
            # Extract calibration values
            def get_value(key):
                return calib[key]['value'] if isinstance(calib[key], dict) else calib[key]
            
            calibration = {
                'screenW': int(get_value('screenW')),
                'screenH': int(get_value('screenH')),
                'pitch': float(get_value('pitch')),
                'slope': float(get_value('slope')),
                'center': float(get_value('center')),
                'DPI': float(get_value('DPI')),
                'fringe': float(get_value('fringe')),
            }
            
            self.message_queue.put(("log", f"Loaded calibration: {calibration['screenW']}x{calibration['screenH']}"))
            return calibration
            
        except Exception as e:
            self.message_queue.put(("log", f"Error loading calibration: {str(e)}"))
            return None
            
    def get_codec_settings(self):
        """Get codec settings based on selected output format"""
        codec = self.output_codec.get()
        
        if codec == "H.264":
            return {
                'fourcc': cv2.VideoWriter_fourcc(*'mp4v'),
                'extension': '.mp4',
                'ffmpeg_codec': 'libx264',
                'pixel_format': 'yuv420p',
                'description': 'H.264/AVC (YUV 4:2:0)'
            }
        elif codec == "H.265 (HEVC)":
            return {
                'fourcc': cv2.VideoWriter_fourcc(*'mp4v'),
                'extension': '.mp4',
                'ffmpeg_codec': 'libx265',
                'pixel_format': 'yuv420p',
                'description': 'H.265/HEVC (YUV 4:2:0)'
            }
        elif codec == "ProRes 422":
            return {
                'fourcc': cv2.VideoWriter_fourcc(*'mp4v'),
                'extension': '.mov',
                'ffmpeg_codec': 'prores_ks',
                'pixel_format': 'yuv422p10le',
                'description': 'Apple ProRes 422 (YUV 4:2:2)'
            }
        elif codec == "H.264 YUV 4:4:4":
            return {
                'fourcc': cv2.VideoWriter_fourcc(*'mp4v'),
                'extension': '.mp4',
                'ffmpeg_codec': 'libx264',
                'pixel_format': 'yuv444p',
                'description': 'H.264/AVC (YUV 4:4:4)'
            }
        elif codec == "H.265 YUV 4:4:4":
            return {
                'fourcc': cv2.VideoWriter_fourcc(*'mp4v'),
                'extension': '.mp4',
                'ffmpeg_codec': 'libx265',
                'pixel_format': 'yuv444p',
                'description': 'H.265/HEVC (YUV 4:4:4)'
            }
        elif codec == "ProRes 4444":
            return {
                'fourcc': cv2.VideoWriter_fourcc(*'mp4v'),
                'extension': '.mov',
                'ffmpeg_codec': 'prores_ks',
                'pixel_format': 'yuva444p10le',
                'description': 'Apple ProRes 4444 (YUV 4:4:4:4 + Alpha)'
            }
        else:
            # Default to H.264
            return {
                'fourcc': cv2.VideoWriter_fourcc(*'mp4v'),
                'extension': '.mp4',
                'ffmpeg_codec': 'libx264',
                'pixel_format': 'yuv420p',
                'description': 'H.264/AVC (YUV 4:2:0)'
            }
            
    def convert_frame(self, frame, calibration, quilt_cols, quilt_rows, quilt_aspect):
        """Convert a single frame from quilt to display format"""
        height, width = frame.shape[:2]
        
        # Get display dimensions from calibration
        display_width = calibration['screenW']
        display_height = calibration['screenH']
        
        # Create output frame
        output_frame = np.zeros((display_height, display_width, 3), dtype=np.uint8)
        
        # Calculate shader parameters
        pitch = calibration['pitch']
        slope = calibration['slope']
        center = calibration['center']
        DPI = calibration['DPI']
        
        screenInches = display_width / DPI
        pitchCalc = pitch * screenInches * math.cos(math.atan(1.0 / slope))
        tilt = display_height / (display_width * slope)
        
        # Process each pixel
        for y in range(display_height):
            for x in range(display_width):
                # Normalize coordinates
                coord_x = x / display_width
                coord_y = y / display_height
                
                # Calculate view angle
                a = (coord_x + coord_y * tilt) * pitchCalc - center
                a = (a + 0.5) % 1.0
                
                # Map to quilt coordinates
                view_index = a * quilt_cols * quilt_rows
                tile_y = int(view_index // quilt_cols)
                tile_x = int((quilt_cols - 1) - (view_index % quilt_cols))
                
                # Ensure tiles are within bounds
                tile_x = max(0, min(quilt_cols - 1, tile_x))
                tile_y = max(0, min(quilt_rows - 1, tile_y))
                
                # Calculate source coordinates in the quilt
                tile_width = width // quilt_cols
                tile_height = height // quilt_rows
                
                source_x = int(tile_x * tile_width + coord_x * tile_width)
                source_y = int(tile_y * tile_height + coord_y * tile_height)
                
                # Ensure source coordinates are within bounds
                source_x = max(0, min(width - 1, source_x))
                source_y = max(0, min(height - 1, source_y))
                
                # Copy pixel
                output_frame[y, x] = frame[source_y, source_x]
                
        return output_frame
        
    def encode_with_ffmpeg(self, frames_dir, output_file, fps, codec_settings):
        """Encode frames to video using FFmpeg"""
        try:
            # Build FFmpeg command
            input_pattern = os.path.join(frames_dir, "frame_%06d.png")
            
            cmd = [
                'ffmpeg', '-y',  # -y to overwrite output file
                '-framerate', str(fps),
                '-i', input_pattern,
                '-c:v', codec_settings['ffmpeg_codec'],
            ]
            
            # Add codec-specific settings
            if codec_settings['ffmpeg_codec'] == 'libx264':
                if codec_settings['pixel_format'] == 'yuv444p':
                    # H.264 YUV 4:4:4 settings
                    cmd.extend(['-crf', '15', '-preset', 'medium', '-profile:v', 'high444'])
                else:
                    # Regular H.264 settings
                    cmd.extend(['-crf', '18', '-preset', 'medium'])
            elif codec_settings['ffmpeg_codec'] == 'libx265':
                if codec_settings['pixel_format'] == 'yuv444p':
                    # H.265 YUV 4:4:4 settings  
                    cmd.extend(['-crf', '17', '-preset', 'medium'])
                else:
                    # Regular H.265 settings
                    cmd.extend(['-crf', '20', '-preset', 'medium'])
            elif codec_settings['ffmpeg_codec'] == 'prores_ks':
                if 'yuva444p10le' in codec_settings['pixel_format']:
                    # ProRes 4444
                    cmd.extend(['-profile:v', '4'])
                else:
                    # ProRes 422
                    cmd.extend(['-profile:v', '2'])
                    
            # Add pixel format
            cmd.extend(['-pix_fmt', codec_settings['pixel_format'], output_file])
            
            self.message_queue.put(("log", f"FFmpeg command: {' '.join(cmd)}"))
            self.message_queue.put(("log", f"Using pixel format: {codec_settings['pixel_format']}"))
            
            # Run FFmpeg
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if process.returncode == 0:
                return True
            else:
                self.message_queue.put(("log", f"FFmpeg error: {process.stderr}"))
                return False
                
        except FileNotFoundError:
            self.message_queue.put(("log", "FFmpeg not found. Please install FFmpeg or add it to PATH"))
            return False
        except subprocess.TimeoutExpired:
            self.message_queue.put(("log", "FFmpeg encoding timed out"))
            return False
        except Exception as e:
            self.message_queue.put(("log", f"FFmpeg encoding error: {str(e)}"))
            return False
            
    def convert_video(self):
        """Main conversion function running in separate thread"""
        try:
            quilt_file = self.quilt_file.get()
            calib_file = self.calibration_file.get()
            output_file = self.output_file.get()
            
            self.message_queue.put(("log", f"Starting conversion of {quilt_file}"))
            
            # Parse quilt parameters
            quilt_cols, quilt_rows, quilt_aspect = self.parse_quilt_filename(quilt_file)
            self.message_queue.put(("log", f"Quilt parameters: {quilt_cols}x{quilt_rows}, aspect {quilt_aspect}"))
            
            # Load calibration
            calibration = self.load_calibration(calib_file)
            if not calibration:
                self.message_queue.put(("log", "Failed to load calibration data"))
                self.message_queue.put(("done", False))
                return
                
            # Open video file
            cap = cv2.VideoCapture(quilt_file)
            if not cap.isOpened():
                self.message_queue.put(("log", "Error: Could not open video file"))
                self.message_queue.put(("done", False))
                return
                
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            self.message_queue.put(("log", f"Video properties: {frame_count} frames at {fps} FPS"))
            
            # Get codec settings
            codec_settings = self.get_codec_settings()
            self.message_queue.put(("log", f"Using codec: {codec_settings['description']}"))
            
            # Force FFmpeg for YUV 4:4:4 formats (OpenCV doesn't handle them well)
            force_ffmpeg = codec_settings['pixel_format'] in ['yuv444p', 'yuva444p10le', 'yuv422p10le']
            
            if force_ffmpeg:
                self.message_queue.put(("log", "Using FFmpeg for high-quality YUV format"))
                use_ffmpeg = True
                temp_frames_dir = None
            else:
                # Set up output video writer
                fourcc = codec_settings['fourcc']
                out = cv2.VideoWriter(output_file, fourcc, fps, 
                                    (calibration['screenW'], calibration['screenH']))
                
                # Check if OpenCV writer was successful
                if not out.isOpened():
                    self.message_queue.put(("log", f"Warning: OpenCV writer failed, will try FFmpeg fallback"))
                    use_ffmpeg = True
                    temp_frames_dir = None
                else:
                    use_ffmpeg = False
            
            # If using FFmpeg fallback, create temporary directory for frames
            if use_ffmpeg:
                import tempfile
                temp_frames_dir = tempfile.mkdtemp()
                self.message_queue.put(("log", f"Using temporary directory: {temp_frames_dir}"))
                frame_files = []
            
            # Process frames
            frame_num = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Convert frame
                converted_frame = self.convert_frame(frame, calibration, quilt_cols, quilt_rows, quilt_aspect)
                
                if use_ffmpeg:
                    # Save frame as image for FFmpeg
                    frame_filename = os.path.join(temp_frames_dir, f"frame_{frame_num:06d}.png")
                    cv2.imwrite(frame_filename, converted_frame)
                    frame_files.append(frame_filename)
                else:
                    # Write frame directly with OpenCV
                    out.write(converted_frame)
                
                frame_num += 1
                progress = (frame_num / frame_count) * 100
                self.message_queue.put(("progress", progress))
                
                if frame_num % 10 == 0:  # Update status every 10 frames
                    self.message_queue.put(("status", f"Processing frame {frame_num}/{frame_count}"))
                    
            # Clean up video capture
            cap.release()
            if not use_ffmpeg:
                out.release()
                
            # If using FFmpeg, encode the frames
            if use_ffmpeg:
                self.message_queue.put(("log", "Encoding video with FFmpeg..."))
                self.message_queue.put(("status", "Encoding final video..."))
                
                if self.encode_with_ffmpeg(temp_frames_dir, output_file, fps, codec_settings):
                    self.message_queue.put(("log", "FFmpeg encoding completed successfully"))
                else:
                    self.message_queue.put(("log", "FFmpeg encoding failed"))
                    self.message_queue.put(("done", False))
                    return
                    
                # Clean up temporary files
                import shutil
                shutil.rmtree(temp_frames_dir)
                self.message_queue.put(("log", "Temporary files cleaned up"))
            
            self.message_queue.put(("log", f"Conversion completed successfully!"))
            self.message_queue.put(("log", f"Output saved to: {output_file}"))
            self.message_queue.put(("done", True))
            
        except Exception as e:
            self.message_queue.put(("log", f"Error during conversion: {str(e)}"))
            self.message_queue.put(("done", False))
            
    def conversion_complete(self, success):
        """Called when conversion is complete"""
        if success:
            self.status_var.set("Conversion completed successfully!")
            self.progress_var.set(100)
            messagebox.showinfo("Success", "Video conversion completed successfully!")
        else:
            self.status_var.set("Conversion failed")
            self.progress_var.set(0)
            messagebox.showerror("Error", "Video conversion failed. Check the log for details.")
            
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        # Check if running in virtual environment (recommended)
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("Running in virtual environment ✓")
        else:
            print("Warning: Not running in virtual environment. Consider running setup.bat first.")
        
        # Test imports
        try:
            import cv2
            print("OpenCV imported successfully ✓")
        except ImportError as e:
            print(f"ERROR: OpenCV not found: {e}")
            print("Please run: pip install opencv-python")
            input("Press Enter to continue anyway...")
        
        try:
            import numpy as np
            print("NumPy imported successfully ✓")
        except ImportError as e:
            print(f"ERROR: NumPy not found: {e}")
            print("Please run: pip install numpy")
            input("Press Enter to continue anyway...")
            
        try:
            from PIL import Image
            print("Pillow imported successfully ✓")
        except ImportError as e:
            print(f"ERROR: Pillow not found: {e}")
            print("Please run: pip install Pillow")
            input("Press Enter to continue anyway...")
        
        # Create and run the application
        print("Starting GUI application...")
        app = QuiltConverter()
        app.run()
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()