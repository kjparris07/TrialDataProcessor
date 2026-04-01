"""
Trial Data Processor - GUI Application
Modern blue Python-themed interface for processing trial data
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
from pathlib import Path
import pandas as pd
import threading

# Import the processing logic from the main script
from process_trial_data import TrialDataProcessor

class TrialDataProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Trial Data Processor")
        self.root.geometry("700x550")
        self.root.resizable(False, False)
        
        # Python blue color scheme
        self.bg_color = "#2B5B84"  # Dark blue
        self.accent_color = "#FFD43B"  # Python yellow
        self.button_color = "#4A90C8"  # Medium blue
        self.text_color = "#FFFFFF"  # White
        self.entry_bg = "#F0F0F0"  # Light gray
        
        self.root.configure(bg=self.bg_color)
        
        # Variables
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.gender_file = tk.StringVar()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        
        # Title
        title_frame = tk.Frame(self.root, bg=self.bg_color)
        title_frame.pack(pady=20)
        
        title_label = tk.Label(
            title_frame,
            text="🐍 Trial Data Processor",
            font=("Segoe UI", 24, "bold"),
            bg=self.bg_color,
            fg=self.accent_color
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Process and analyze trial data with ease",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg=self.text_color
        )
        subtitle_label.pack()
        
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(padx=40, pady=10, fill=tk.BOTH, expand=True)
        
        # Input folder selection
        self.create_file_selector(
            main_frame,
            "Trial Data Folder (Required):",
            self.input_folder,
            self.browse_input_folder,
            row=0
        )
        
        # Output folder selection
        self.create_file_selector(
            main_frame,
            "Output Folder (Required):",
            self.output_folder,
            self.browse_output_folder,
            row=1
        )
        
        # Gender file selection (optional)
        self.create_file_selector(
            main_frame,
            "Gender File (Optional):",
            self.gender_file,
            self.browse_gender_file,
            row=2,
            optional=True
        )
        
        # Process button
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(pady=20)
        
        self.process_button = tk.Button(
            button_frame,
            text="▶ Process Data",
            font=("Segoe UI", 12, "bold"),
            bg=self.button_color,
            fg=self.text_color,
            activebackground=self.accent_color,
            activeforeground=self.bg_color,
            relief=tk.FLAT,
            padx=40,
            pady=12,
            cursor="hand2",
            command=self.process_data
        )
        self.process_button.pack()
        
        # Progress bar
        self.progress_frame = tk.Frame(self.root, bg=self.bg_color)
        self.progress_frame.pack(pady=10, padx=40, fill=tk.X)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=600
        )
        self.progress_bar.pack()
        
        # Status label
        self.status_label = tk.Label(
            self.root,
            text="Ready to process data",
            font=("Segoe UI", 9),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.status_label.pack(pady=5)
        
        # Footer
        footer_label = tk.Label(
            self.root,
            text="Powered by Python 🐍",
            font=("Segoe UI", 8),
            bg=self.bg_color,
            fg=self.accent_color
        )
        footer_label.pack(side=tk.BOTTOM, pady=10)
    
    def create_file_selector(self, parent, label_text, variable, command, row, optional=False):
        """Create a file/folder selector row"""
        frame = tk.Frame(parent, bg=self.bg_color)
        frame.pack(pady=10, fill=tk.X)
        
        # Label
        label_frame = tk.Frame(frame, bg=self.bg_color)
        label_frame.pack(anchor=tk.W)
        
        label = tk.Label(
            label_frame,
            text=label_text,
            font=("Segoe UI", 10, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        label.pack(side=tk.LEFT)
        
        if optional:
            optional_label = tk.Label(
                label_frame,
                text=" (leave empty for NaN)",
                font=("Segoe UI", 8),
                bg=self.bg_color,
                fg=self.accent_color
            )
            optional_label.pack(side=tk.LEFT)
        
        # Entry and button frame
        entry_frame = tk.Frame(frame, bg=self.bg_color)
        entry_frame.pack(fill=tk.X, pady=5)
        
        entry = tk.Entry(
            entry_frame,
            textvariable=variable,
            font=("Segoe UI", 9),
            bg=self.entry_bg,
            relief=tk.FLAT,
            width=50
        )
        entry.pack(side=tk.LEFT, padx=(0, 10), ipady=5)
        
        browse_button = tk.Button(
            entry_frame,
            text="Browse...",
            font=("Segoe UI", 9),
            bg=self.button_color,
            fg=self.text_color,
            activebackground=self.accent_color,
            activeforeground=self.bg_color,
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2",
            command=command
        )
        browse_button.pack(side=tk.LEFT)
    
    def browse_input_folder(self):
        """Browse for input folder"""
        folder = filedialog.askdirectory(title="Select Trial Data Folder")
        if folder:
            self.input_folder.set(folder)
    
    def browse_output_folder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
    
    def browse_gender_file(self):
        """Browse for gender file"""
        file = filedialog.askopenfilename(
            title="Select Gender File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file:
            self.gender_file.set(file)
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def process_data(self):
        """Process the trial data"""
        # Validate inputs
        if not self.input_folder.get():
            messagebox.showerror("Error", "Please select the Trial Data Folder")
            return
        
        if not self.output_folder.get():
            messagebox.showerror("Error", "Please select the Output Folder")
            return
        
        if not os.path.exists(self.input_folder.get()):
            messagebox.showerror("Error", "Trial Data Folder does not exist")
            return
        
        if not os.path.exists(self.output_folder.get()):
            messagebox.showerror("Error", "Output Folder does not exist")
            return
        
        # Check if gender file is provided and exists
        gender_file_path = self.gender_file.get()
        if gender_file_path and not os.path.exists(gender_file_path):
            messagebox.showerror("Error", "Gender file does not exist")
            return
        
        # Disable button and start progress
        self.process_button.config(state=tk.DISABLED)
        self.progress_bar.start(10)
        
        # Run processing in separate thread
        thread = threading.Thread(target=self._run_processing)
        thread.start()
    
    def _run_processing(self):
        """Run the processing in a separate thread"""
        try:
            self.update_status("Processing trial data...")
            
            # Set up paths
            data_dir = Path(self.input_folder.get())
            output_dir = Path(self.output_folder.get())
            gender_file = Path(self.gender_file.get()) if self.gender_file.get() else None
            
            # Output files
            output_detailed = output_dir / "processed_data.csv"
            
            # Initialize processor
            self.update_status("Initializing processor...")
            processor = TrialDataProcessor(str(data_dir), str(gender_file) if gender_file else None)
            
            # Process all files
            self.update_status("Processing trial files...")
            NO_COLLISIONS, ONE_COLLISION, MULTIPLE_COLLISIONS = processor.process_all_files()
            
            # Save detailed results
            self.update_status("Saving detailed and collision results...")
            processor.save_results(NO_COLLISIONS, ONE_COLLISION, MULTIPLE_COLLISIONS, str(output_detailed))
            
            # Success
            self.root.after(0, self._processing_complete, output_dir)
            
        except Exception as e:
            self.root.after(0, self._processing_error, str(e))
    
    def _processing_complete(self, output_dir):
        """Called when processing completes successfully"""
        self.progress_bar.stop()
        self.process_button.config(state=tk.NORMAL)
        self.update_status("Processing complete!")
        
        messagebox.showinfo(
            "Success",
            f"Processing complete!\n\nOutput files saved to:\n{output_dir}\n"
        )
    
    def _processing_error(self, error_message):
        """Called when processing encounters an error"""
        self.progress_bar.stop()
        self.process_button.config(state=tk.NORMAL)
        self.update_status("Error occurred")
        
        messagebox.showerror("Processing Error", f"An error occurred:\n\n{error_message}")


def main():
    root = tk.Tk()
    app = TrialDataProcessorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
