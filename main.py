import customtkinter as ctk
import os
import threading
from tkinter import filedialog, messagebox
import yt_dlp
import subprocess
import sys

# --- Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ultimate Media Downloader")
        self.geometry("700x550")
        self.resizable(False, False)

        # Grid configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # --- Header ---
        self.label_title = ctk.CTkLabel(self, text="YouTube & Spotify Downloader", font=("Roboto", 24, "bold"))
        self.label_title.grid(row=0, column=0, pady=(20, 10), sticky="ew")

        # --- Input Area ---
        self.frame_input = ctk.CTkFrame(self)
        self.frame_input.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.entry_url = ctk.CTkEntry(self.frame_input, placeholder_text="Paste YouTube or Spotify URL here...")
        self.entry_url.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=10)

        # --- Options Area ---
        self.frame_options = ctk.CTkFrame(self)
        self.frame_options.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Format Selection
        self.label_format = ctk.CTkLabel(self.frame_options, text="Format:")
        self.label_format.grid(row=0, column=0, padx=10, pady=10)
        
        self.format_var = ctk.StringVar(value="mp4")
        self.radio_mp4 = ctk.CTkRadioButton(self.frame_options, text="MP4 (Video)", variable=self.format_var, value="mp4")
        self.radio_mp4.grid(row=0, column=1, padx=10, pady=10)
        self.radio_mp3 = ctk.CTkRadioButton(self.frame_options, text="MP3 (Audio)", variable=self.format_var, value="mp3")
        self.radio_mp3.grid(row=0, column=2, padx=10, pady=10)

        # Save Location
        self.btn_browse = ctk.CTkButton(self.frame_options, text="Select Folder", command=self.browse_folder)
        self.btn_browse.grid(row=0, column=3, padx=20, pady=10)
        
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.label_path = ctk.CTkLabel(self.frame_options, text=f"Save to: {os.path.basename(self.download_path)}", text_color="gray")
        self.label_path.grid(row=1, column=0, columnspan=4, padx=10, pady=(0, 10))

        # --- Progress Area ---
        self.frame_progress = ctk.CTkFrame(self)
        self.frame_progress.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(self.frame_progress)
        self.progress_bar.pack(fill="x", padx=20, pady=(20, 10))
        self.progress_bar.set(0)

        self.label_status = ctk.CTkLabel(self.frame_progress, text="Ready")
        self.label_status.pack(pady=(0, 10))

        # --- Action Button ---
        self.btn_download = ctk.CTkButton(self, text="START DOWNLOAD", height=50, font=("Roboto", 16, "bold"), command=self.start_download_thread)
        self.btn_download.grid(row=4, column=0, padx=20, pady=20, sticky="ew")
        
        # --- Logs ---
        self.textbox_log = ctk.CTkTextbox(self, height=100)
        self.textbox_log.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.log_message("Welcome! Please make sure FFmpeg is installed on your system.")

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.download_path = folder_selected
            self.label_path.configure(text=f"Save to: {os.path.basename(self.download_path)}")

    def log_message(self, message):
        self.textbox_log.insert("end", f"> {message}\n")
        self.textbox_log.see("end")

    def update_status(self, text):
        self.label_status.configure(text=text)

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                p = d.get('_percent_str', '0%').replace('%','')
                self.progress_bar.set(float(p) / 100)
                self.update_status(f"Downloading: {d.get('_percent_str')} | Speed: {d.get('_speed_str')}")
            except:
                pass
        elif d['status'] == 'finished':
            self.progress_bar.set(1)
            self.update_status("Download Complete. Processing...")

    def start_download_thread(self):
        url = self.entry_url.get()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        self.btn_download.configure(state="disabled")
        self.progress_bar.set(0)
        
        # Run download in a separate thread to keep GUI responsive
        threading.Thread(target=self.download_logic, args=(url,)).start()

    def download_logic(self, url):
        try:
            if "open.spotify.com" in url: # <-- THIS IS CORRECT
                self.download_spotify(url)
            else:
                self.download_youtube(url)
            # ... rest of the code
            
            self.log_message("All tasks finished successfully!")
            messagebox.showinfo("Success", "Download Complete!")

        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.btn_download.configure(state="normal")
            self.update_status("Ready")

    def download_spotify(self, url):
        self.log_message("Detected Spotify URL. Using SpotDL...")
        self.update_status("Initializing SpotDL (This may take a moment)...")
        
        # SpotDL is best run via subprocess as it handles its own complex logic
        # We download to the selected path
        os.chdir(self.download_path)
        
        cmd = ["spotdl", url]
        
        # If user wants MP3 specifically (SpotDL defaults to mp3 usually, but we ensure)
        # SpotDL automatically handles metadata and high quality audio
        
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self.log_message(output.strip())
                # Rough progress estimation for Spotify since spotdl output varies
                if "Downloading" in output:
                    self.progress_bar.set(0.5)
                    
        if process.returncode != 0:
            raise Exception("SpotDL failed. Make sure 'spotdl' is installed via pip.")

    def download_youtube(self, url):
        self.log_message("Detected YouTube URL. Using yt-dlp...")
        format_type = self.format_var.get()
        
        ydl_opts = {
            'logger': None,
            'progress_hooks': [self.progress_hook],
            'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
            'ignoreerrors': True, # Skip unavailable videos in playlists
        }

        if format_type == "mp3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
            self.log_message("Mode: Audio (MP3) - High Quality")
        else:
            # MP4 Video - We aim for 1080p (Best video) + Best Audio merged
            ydl_opts.update({
                'format': 'bestvideo[height<=1080]+bestaudio/best[ext=m4a]/best[ext=mp4]/best',
                 'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            })
            self.log_message("Mode: Video (MP4) - 1080p Max")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # This supports single videos AND playlists automatically
            ydl.download([url])

if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()