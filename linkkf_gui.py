#!/usr/bin/env python3
"""
LinkKF Video Downloader GUI - Dark Cyber Theme

A GUI application for downloading videos from kr.linkkf.net
Supports batch downloading of multiple videos.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import time
import re

# Import our downloader class
from linkkf_downloader import LinkKFDownloader


class LinkKFGUI:
    """GUI application for LinkKF video downloader with dark cyber theme."""
    
    def __init__(self) -> None:
        """Initialize the GUI application."""
        self.root = tk.Tk()
        self.root.title("🎬 Linkkf 다운로더 v1.0 By noName_Come")
        self.root.geometry("950x900")  # 기본 크기 (세로 850→900)
        self.root.minsize(750, 800)    # 최소 크기 (세로 750→800)
        
        # Set window icon
        try:
            icon_path = Path("favicon.ico")
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            # If favicon.ico is not found or can't be loaded, continue without icon
            pass
        
        # Dark theme colors
        self.colors = {
            'bg': '#0D1117',           # 매우 어두운 배경
            'fg': '#00FF41',           # 매트릭스 초록
            'secondary_bg': '#161B22',  # 약간 밝은 배경
            'accent': '#00D4AA',       # 시아노 액센트
            'success': '#00FF41',      # 성공 초록
            'error': '#FF4444',        # 에러 빨강
            'warning': '#FFA500',      # 경고 주황
            'info': '#00BFFF',         # 정보 파랑
            'button_bg': '#21262D',    # 버튼 배경
            'entry_bg': '#0D1117',     # 입력창 배경
            'text_area_bg': '#010409'  # 텍스트 영역 배경
        }
        
        # Configure root window
        self.root.configure(bg=self.colors['bg'])
        
        # Variables
        self.output_dir = tk.StringVar(value="./downloads")
        self.is_downloading = False
        self.download_queue = queue.Queue()
        self.log_queue = queue.Queue()
        self.download_stats = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'current': ''
        }
        
        self.setup_styles()
        self.setup_ui()
        self.setup_logging()
        
        # Start log processing thread
        self.process_logs()
        
        # Center window on screen
        self.center_window()
    
    def setup_styles(self) -> None:
        """Set up custom dark cyber styles for the GUI."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure dark theme styles
        style.configure('Dark.TFrame',
                       background=self.colors['bg'],
                       borderwidth=0)
        
        style.configure('DarkSection.TLabelframe',
                       background=self.colors['bg'],
                       foreground=self.colors['fg'],
                       borderwidth=2,
                       relief='solid',
                       labelmargins=(10, 5, 10, 5))
        
        style.configure('DarkSection.TLabelframe.Label',
                       background=self.colors['bg'],
                       foreground=self.colors['accent'],
                       font=('맑은 고딕', 12, 'bold'))
        
        style.configure('CyberTitle.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['fg'],
                       font=('맑은 고딕', 22, 'bold'))
        
        style.configure('CyberDesc.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['accent'],
                       font=('맑은 고딕', 11))
        
        style.configure('CyberHeading.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['fg'],
                       font=('맑은 고딕', 11, 'bold'))
        
        style.configure('CyberInfo.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['info'],
                       font=('맑은 고딕', 10))
        
        # Button styles
        style.configure('Cyber.TButton',
                       background=self.colors['button_bg'],
                       foreground=self.colors['fg'],
                       font=('맑은 고딕', 10, 'bold'),
                       borderwidth=1,
                       relief='solid',
                       focuscolor='none')
        
        style.map('Cyber.TButton',
                 background=[('active', self.colors['secondary_bg']),
                           ('pressed', self.colors['accent'])])
        
        style.configure('CyberSuccess.TButton',
                       background=self.colors['button_bg'],
                       foreground=self.colors['success'],
                       font=('맑은 고딕', 11, 'bold'),
                       borderwidth=2,
                       relief='solid')
        
        style.configure('CyberDanger.TButton',
                       background=self.colors['button_bg'],
                       foreground=self.colors['error'],
                       font=('맑은 고딕', 10, 'bold'),
                       borderwidth=1,
                       relief='solid')
        
        # Entry styles
        style.configure('Cyber.TEntry',
                       background=self.colors['entry_bg'],
                       foreground=self.colors['fg'],
                       font=('맑은 고딕', 10),
                       borderwidth=1,
                       relief='solid',
                       insertcolor=self.colors['fg'])
        
        # Progress bar style
        style.configure('Cyber.Horizontal.TProgressbar',
                       background=self.colors['success'],
                       troughcolor=self.colors['secondary_bg'],
                       borderwidth=1,
                       lightcolor=self.colors['success'],
                       darkcolor=self.colors['success'])
    
    def center_window(self) -> None:
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self) -> None:
        """Set up the user interface with dark cyber theme."""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame', padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Simple header (without ASCII art)
        header_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        header_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky=(tk.W, tk.E))
        header_frame.columnconfigure(0, weight=1)
        
        # Simple title
        title_label = tk.Label(
            header_frame,
            text="🎬 LinkkF 애니 다운로더",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('맑은 고딕', 18, 'bold')
        )
        title_label.grid(row=0, column=0, pady=(0, 5))
        
        desc_label = ttk.Label(
            header_frame,
            text="█ 일본 애니를 해킹하듯 빠르게 다운로드 █",
            style='CyberDesc.TLabel'
        )
        desc_label.grid(row=1, column=0)
        
        # Output directory section with cyber styling
        dir_section = ttk.LabelFrame(
            main_frame,
            text="📁 대상 디렉토리",
            style='DarkSection.TLabelframe',
            padding="15"
        )
        dir_section.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        dir_section.columnconfigure(1, weight=1)
        
        ttk.Label(
            dir_section,
            text="▶ 경로:",
            style='CyberHeading.TLabel'
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        
        self.dir_entry = ttk.Entry(
            dir_section,
            textvariable=self.output_dir,
            style='Cyber.TEntry',
            width=60
        )
        self.dir_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 15))
        
        browse_btn = ttk.Button(
            dir_section,
            text="🔍 탐색",
            command=self.browse_directory,
            style='Cyber.TButton'
        )
        browse_btn.grid(row=0, column=2)
        
        # URL input section with matrix styling
        url_section = ttk.LabelFrame(
            main_frame,
            text="🔗 대상 URL 매트릭스",
            style='DarkSection.TLabelframe',
            padding="15"
        )
        url_section.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        url_section.columnconfigure(0, weight=1)
        url_section.rowconfigure(1, weight=1)
        
        # Instructions with cyber styling
        instruction_frame = tk.Frame(url_section, bg=self.colors['bg'])
        instruction_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        instruction_frame.columnconfigure(0, weight=1)
        
        ttk.Label(
            instruction_frame,
            text="▶ URL 주입 (최대 25개 대상):",
            style='CyberHeading.TLabel'
        ).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(
            instruction_frame,
            text="▶ 형식: https://linkkf.live/player/v[번호]-sub-[번호]/",
            style='CyberInfo.TLabel'
        ).grid(row=1, column=0, sticky=tk.W)
        
        # URL text area with dark styling
        url_frame = tk.Frame(url_section, bg=self.colors['bg'])
        url_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        url_frame.columnconfigure(0, weight=1)
        url_frame.rowconfigure(0, weight=1)
        
        self.url_text = scrolledtext.ScrolledText(
            url_frame,
            height=6,
            wrap=tk.WORD,
            font=('맑은 고딕', 10),
            bg=self.colors['text_area_bg'],
            fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            selectbackground=self.colors['accent'],
            selectforeground=self.colors['bg'],
            relief=tk.SOLID,
            borderwidth=2
        )
        self.url_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Placeholder text with cyber theme
        placeholder_text = """# 대상 URL 주입 구역
# 한 줄에 하나씩 URL을 입력하세요

https://linkkf.live/player/v00000-sub-1/
https://linkkf.live/player/v00000-sub-2/

# 최대 25개 동시 대상
# 사이버 다운로드 준비 완료..."""
        
        self.url_text.insert('1.0', placeholder_text)
        self.url_text.bind('<FocusIn>', self.clear_placeholder)
        self.url_text.bind('<FocusOut>', self.restore_placeholder)
        self.url_text.config(fg=self.colors['info'])
        
        # Control buttons with cyber styling
        button_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        self.download_btn = ttk.Button(
            button_frame,
            text="🚀 다운로드 시작",
            command=self.start_download,
            style='CyberSuccess.TButton',
            width=20
        )
        self.download_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_btn = ttk.Button(
            button_frame,
            text="⏹️ 중단",
            command=self.stop_download,
            state=tk.DISABLED,
            style='CyberDanger.TButton',
            width=12
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.clear_btn = ttk.Button(
            button_frame,
            text="🗑️ URL 지우기",
            command=self.clear_urls,
            style='Cyber.TButton',
            width=14
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.clear_log_btn = ttk.Button(
            button_frame,
            text="📄 로그 지우기",
            command=self.clear_log,
            style='Cyber.TButton',
            width=14
        )
        self.clear_log_btn.pack(side=tk.LEFT)
        
        # Progress section with cyber design
        progress_section = ttk.LabelFrame(
            main_frame,
            text="📊 사이버 다운로드 매트릭스",
            style='DarkSection.TLabelframe',
            padding="15"
        )
        progress_section.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        progress_section.columnconfigure(0, weight=1)
        progress_section.rowconfigure(2, weight=1)
        
        # Progress bar with cyber style
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_section,
            variable=self.progress_var,
            maximum=100,
            length=500,
            style='Cyber.Horizontal.TProgressbar'
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.progress_label = tk.Label(
            progress_section,
            text="█ 시스템 준비 완료 █",
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('맑은 고딕', 11, 'bold')
        )
        self.progress_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 15))
        
        # Log area with matrix-style scrolling
        log_frame = tk.Frame(progress_section, bg=self.colors['bg'])
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            state=tk.DISABLED,
            font=('맑은 고딕', 10),
            bg=self.colors['text_area_bg'],
            fg=self.colors['fg'],
            relief=tk.SOLID,
            borderwidth=2,
            wrap=tk.WORD
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for colored output
        self.log_text.tag_configure('success', foreground=self.colors['success'], font=('맑은 고딕', 10, 'bold'))
        self.log_text.tag_configure('error', foreground=self.colors['error'], font=('맑은 고딕', 10, 'bold'))
        self.log_text.tag_configure('warning', foreground=self.colors['warning'], font=('맑은 고딕', 10, 'bold'))
        self.log_text.tag_configure('info', foreground=self.colors['info'], font=('맑은 고딕', 10))
        
        # Status bar with cyber styling
        status_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        status_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(15, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="█ 다운로더 시스템 온라인 █")
        status_bar = tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg=self.colors['secondary_bg'],
            fg=self.colors['accent'],
            font=('맑은 고딕', 10, 'bold'),
            relief=tk.SOLID,
            borderwidth=1,
            padx=10,
            pady=5
        )
        status_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
    
    def setup_logging(self) -> None:
        """Set up logging to capture downloader output."""
        pass
    
    def clear_placeholder(self, event) -> None:
        """Clear placeholder text when text widget gets focus."""
        if self.url_text.get('1.0', tk.END).strip().startswith('# 대상 URL'):
            self.url_text.delete('1.0', tk.END)
            self.url_text.config(fg=self.colors['fg'])
    
    def restore_placeholder(self, event) -> None:
        """Restore placeholder text if text widget is empty."""
        if not self.url_text.get('1.0', tk.END).strip():
            placeholder_text = """# 대상 URL 주입 구역
# 한 줄에 하나씩 URL을 입력하세요

https://linkkf.live/player/v00000-sub-1/
https://linkkf.live/player/v00000-sub-2/

# 최대 25개 동시 대상
# 사이버 다운로드 준비 완료..."""
            self.url_text.insert('1.0', placeholder_text)
            self.url_text.config(fg=self.colors['info'])
    
    def browse_directory(self) -> None:
        """Open directory browser dialog."""
        directory = filedialog.askdirectory(
            initialdir=self.output_dir.get(),
            title="대상 디렉토리를 선택하세요"
        )
        if directory:
            self.output_dir.set(directory)
    
    def clear_urls(self) -> None:
        """Clear the URL text area."""
        self.url_text.delete('1.0', tk.END)
        self.url_text.config(fg=self.colors['fg'])
    
    def clear_log(self) -> None:
        """Clear the log text area."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def log_message(self, message: str, tag: str = 'info') -> None:
        """Add a message to the log with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, full_message, tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def process_logs(self) -> None:
        """Process log messages from the queue."""
        try:
            while True:
                message, tag = self.log_queue.get_nowait()
                self.log_message(message, tag)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_logs)
    
    def validate_urls(self, urls: List[str]) -> List[str]:
        """Validate and filter LinkKF URLs."""
        valid_urls = []
        pattern = r'https://linkkf\.live/player/v\d+-sub-\d+/?'
        
        for url in urls:
            url = url.strip()
            if not url or url.startswith('#'):  # Skip comments
                continue
            
            if re.match(pattern, url):
                if not url.endswith('/'):
                    url += '/'
                valid_urls.append(url)
            else:
                self.log_queue.put((f"█ 잘못된 대상: {url}", 'warning'))
        
        return valid_urls
    
    def get_urls_from_text(self) -> List[str]:
        """Extract URLs from the text widget."""
        text_content = self.url_text.get('1.0', tk.END)
        
        if text_content.strip().startswith('# 대상 URL'):
            return []
        
        lines = text_content.split('\n')
        urls = [line.strip() for line in lines if line.strip()]
        
        return self.validate_urls(urls)
    
    def update_progress(self) -> None:
        """Update progress bar and labels."""
        if self.download_stats['total'] == 0:
            progress = 0
        else:
            progress = (self.download_stats['completed'] + self.download_stats['failed']) / self.download_stats['total'] * 100
        
        self.progress_var.set(progress)
        
        status_text = f"█ 진행률: {self.download_stats['completed'] + self.download_stats['failed']}/{self.download_stats['total']} "
        status_text += f"(✅ {self.download_stats['completed']} 성공, ❌ {self.download_stats['failed']} 실패)"
        
        if self.download_stats['current']:
            status_text += f" - 현재: {self.download_stats['current']}"
        
        self.progress_label.config(text=status_text)
        self.status_var.set(status_text)
    
    def download_worker(self, urls: List[str], output_dir: str) -> None:
        """Worker thread for downloading videos."""
        downloader = LinkKFDownloader(output_dir)
        
        self.download_stats['total'] = len(urls)
        self.download_stats['completed'] = 0
        self.download_stats['failed'] = 0
        
        for i, url in enumerate(urls, 1):
            if not self.is_downloading:
                break
            
            video_id_match = re.search(r'v(\d+)-sub-(\d+)', url)
            if video_id_match:
                video_title = f"대상_{video_id_match.group(1)}_{video_id_match.group(2)}"
            else:
                video_title = f"대상_{i}"
            
            self.download_stats['current'] = video_title
            self.root.after(0, self.update_progress)
            
            self.log_queue.put((f"█ 해킹 시작 {i}/{len(urls)}: {video_title}", 'info'))
            self.log_queue.put((f"█ 대상 URL: {url}", 'info'))
            
            try:
                success = self.download_with_logging(downloader, url)
                
                if success:
                    self.download_stats['completed'] += 1
                    self.log_queue.put((f"█ 해킹 성공: {video_title}", 'success'))
                else:
                    self.download_stats['failed'] += 1
                    self.log_queue.put((f"█ 해킹 실패: {video_title}", 'error'))
                    
            except Exception as e:
                self.download_stats['failed'] += 1
                self.log_queue.put((f"█ 시스템 오류 {video_title}: {str(e)}", 'error'))
            
            self.root.after(0, self.update_progress)
            
            if self.is_downloading and i < len(urls):
                time.sleep(1)
        
        self.download_stats['current'] = ''
        self.root.after(0, self.download_finished)
    
    def download_with_logging(self, downloader: LinkKFDownloader, url: str) -> bool:
        """Download video with custom logging and UTF-8 encoding fix."""
        original_print = print
        
        def custom_print(*args, **kwargs):
            try:
                message = ' '.join(str(arg) for arg in args)
                
                if '✅' in message or '🎉' in message:
                    tag = 'success'
                elif '❌' in message or 'Error' in message or 'Failed' in message:
                    tag = 'error'
                elif '⚠️' in message or 'Warning' in message:
                    tag = 'warning'
                else:
                    tag = 'info'
                
                self.log_queue.put((message, tag))
            except (UnicodeDecodeError, UnicodeEncodeError):
                # Handle encoding issues
                self.log_queue.put(("█ 인코딩 오류 감지됨", 'warning'))
        
        # Replace print function and fix subprocess encoding
        import builtins
        builtins.print = custom_print
        
        # Patch subprocess to handle encoding properly
        original_popen = subprocess.Popen
        def patched_popen(*args, **kwargs):
            if 'encoding' not in kwargs:
                kwargs['encoding'] = 'utf-8'
            if 'errors' not in kwargs:
                kwargs['errors'] = 'ignore'
            return original_popen(*args, **kwargs)
        
        original_run = subprocess.run
        def patched_run(*args, **kwargs):
            if 'encoding' not in kwargs:
                kwargs['encoding'] = 'utf-8'
            if 'errors' not in kwargs:
                kwargs['errors'] = 'ignore'
            return original_run(*args, **kwargs)
        
        subprocess.Popen = patched_popen
        subprocess.run = patched_run
        
        try:
            success = downloader.download_video(url)
            return success
        finally:
            builtins.print = original_print
            subprocess.Popen = original_popen
            subprocess.run = original_run
    
    def start_download(self) -> None:
        """Start the download process."""
        if self.is_downloading:
            return
        
        urls = self.get_urls_from_text()
        if not urls:
            messagebox.showwarning("대상 없음", "최소 하나 이상의 유효한 LinkKF URL을 입력해주세요.")
            return
        
        if len(urls) > 25:
            result = messagebox.askyesno(
                "대상 과다",
                f"{len(urls)}개의 대상이 탐지되었습니다. 해킹에 시간이 오래 걸릴 수 있습니다. 계속하시겠습니까?"
            )
            if not result:
                return
        
        output_dir = self.output_dir.get()
        if not output_dir:
            messagebox.showwarning("디렉토리 없음", "대상 디렉토리를 선택해주세요.")
            return
        
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("디렉토리 오류", f"대상 디렉토리를 생성할 수 없습니다: {e}")
            return
        
        self.is_downloading = True
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.log_message(f"█ 사이버 해킹 시작: {len(urls)}개 대상", 'info')
        self.log_message(f"█ 대상 디렉토리: {output_dir}", 'info')
        
        download_thread = threading.Thread(
            target=self.download_worker,
            args=(urls, output_dir),
            daemon=True
        )
        download_thread.start()
    
    def stop_download(self) -> None:
        """Stop the download process."""
        if not self.is_downloading:
            return
        
        self.is_downloading = False
        self.log_message("█ 사용자에 의해 해킹 중단됨", 'warning')
        self.download_finished()
    
    def download_finished(self) -> None:
        """Handle download completion."""
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        completed = self.download_stats['completed']
        failed = self.download_stats['failed']
        total = self.download_stats['total']
        
        self.log_message(f"█ 사이버 해킹 완료: {completed}/{total} 성공, {failed}/{total} 실패", 'info')
        
        if completed > 0:
            messagebox.showinfo(
                "해킹 완료",
                f"총 {total}개 중 {completed}개의 대상을 성공적으로 다운받았습니다.\n"
                f"저장 위치: {self.output_dir.get()}"
            )
        elif failed > 0:
            messagebox.showwarning(
                "해킹 실패",
                f"모든 {failed}개의 해킹이 실패했습니다. URL을 확인하고 다시 시도해주세요."
            )
        
        self.update_progress()
    
    def run(self) -> None:
        """Run the GUI application."""
        try:
            # Set encoding for Windows console
            if sys.platform == 'win32':
                os.environ['PYTHONIOENCODING'] = 'utf-8'
            
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()


def main() -> None:
    """Main function."""
    try:
        # Set encoding for Windows console
        if sys.platform == 'win32':
            os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        app = LinkKFGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("시스템 오류", f"사이버 시스템을 시작할 수 없습니다: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 