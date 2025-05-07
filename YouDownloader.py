import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Playlist Downloader")
        self.root.geometry("700x600")
        self.video_list = []
        self.check_vars = []

        # Playlist URL input
        self.url_label = ttk.Label(root, text="Playlist URL:")
        self.url_label.pack(pady=5)
        self.url_entry = ttk.Entry(root, width=80)
        self.url_entry.pack(pady=5)

        # Buttons
        self.fetch_button = ttk.Button(root, text="Fetch Playlist", command=self.fetch_playlist)
        self.fetch_button.pack(pady=5)

        self.output_button = ttk.Button(root, text="Select Output Folder", command=self.select_folder)
        self.output_button.pack(pady=5)
        self.output_folder = tk.StringVar(value=os.getcwd())

        self.audio_only = tk.BooleanVar()
        self.audio_check = ttk.Checkbutton(root, text="Download Audio Only", variable=self.audio_only)
        self.audio_check.pack(pady=5)

        self.download_button = ttk.Button(root, text="Download Selected", command=self.start_download_thread)
        self.download_button.pack(pady=10)

        # Playlist list
        self.video_frame = ttk.LabelFrame(root, text="Playlist Videos")
        self.video_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.canvas = tk.Canvas(self.video_frame)
        self.scrollbar = ttk.Scrollbar(self.video_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Log box
        self.log_box = tk.Text(root, height=10, bg="#000", fg="#0f0")
        self.log_box.pack(fill=tk.BOTH, padx=10, pady=5)

    def log(self, msg):
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    def fetch_playlist(self):
        self.video_list.clear()
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        url = self.url_entry.get()
        ydl_opts = {
            'extract_flat': 'in_playlist',
            'quiet': True,
            'force_generic_extractor': False,
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                self.log(f"Fetched playlist: {info.get('title', '')}")
                for i, entry in enumerate(info.get('entries', [])):
                    title = entry.get('title', f"Video {i + 1}")
                    link = entry.get('url')
                    full_url = f"https://www.youtube.com/watch?v={link}" if "youtube.com" not in link else link
                    self.video_list.append((title, full_url))
                    var = tk.BooleanVar(value=True)
                    self.check_vars.append(var)
                    cb = ttk.Checkbutton(self.scrollable_frame, text=title[:80], variable=var)
                    cb.pack(anchor="w", padx=5)
        except Exception as e:
            self.log(f"Error fetching playlist: {e}")

    def start_download_thread(self):
        threading.Thread(target=self.download_selected, daemon=True).start()

    def download_selected(self):
        for i, (title, url) in enumerate(self.video_list):
            if self.check_vars[i].get():
                self.log(f"Starting download: {title}")
                self.download_video_or_audio(url, title)

    def download_video_or_audio(self, url, title):
        def progress_hook(d):
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%').strip()
                self.root.after(0, self.log, f"{title} → {percent}")
            elif d['status'] == 'finished':
                self.root.after(0, self.log, f"{title} → Download complete.")

        ydl_opts = {
            'outtmpl': os.path.join(self.output_folder.get(), '%(title)s.%(ext)s'),
            'format': 'bestaudio/best' if self.audio_only.get() else 'best',
            'quiet': True,
            'progress_hooks': [progress_hook],
            'noplaylist': True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except DownloadError as e:
            self.log(f"Download failed for {title}: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()
