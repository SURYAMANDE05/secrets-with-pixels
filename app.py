"""
app.py - Steganography Desktop Application GUI
==============================================
Secrets within Pixels – The Art of Steganography
A modern, feature-rich Tkinter desktop application for hiding and extracting
messages within image pixels using LSB steganography and AES-Fernet encryption.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional
from PIL import Image, ImageTk

import steganography as stego
import crypto_utils as crypto

# --- Color Palette & Theme Styling ---
THEME = {
    "bg_dark": "#0f172a",        # Slate 900
    "bg_card": "#1e293b",        # Slate 800
    "bg_card_alt": "#334155",    # Slate 700
    "input_bg": "#0f172a",       # Slate 900
    "input_fg": "#f8fafc",       # Slate 50
    "text_primary": "#f8fafc",   # Slate 50
    "text_secondary": "#94a3b8", # Slate 400
    "accent_primary": "#06b6d4", # Cyan 500
    "accent_hover": "#0891b2",   # Cyan 600
    "accent_green": "#10b981",   # Emerald 500
    "accent_amber": "#f59e0b",   # Amber 500
    "accent_red": "#ef4444",     # Red 500
    "border": "#334155",         # Slate 700
}

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"


class SteganographyApp(tk.Tk):
    """Main application window for 'Secrets within Pixels'."""

    def __init__(self):
        super().__init__()
        self.title("Secrets within Pixels – The Art of Steganography")
        self.geometry("960x780")
        self.minsize(880, 680)
        self.configure(bg=THEME["bg_dark"])

        # Try setting window icon if available or standard
        try:
            # High-DPI awareness on Windows
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        # State Variables - Hide Secret
        self.encode_image_path: Optional[str] = None
        self.encode_image_obj: Optional[Image.Image] = None
        self.encode_thumbnail_photo: Optional[ImageTk.PhotoImage] = None
        self.encode_capacity_info: dict = {}

        # State Variables - Extract Secret
        self.decode_image_path: Optional[str] = None
        self.decode_image_obj: Optional[Image.Image] = None
        self.decode_thumbnail_photo: Optional[ImageTk.PhotoImage] = None

        self._configure_styles()
        self._build_header()
        self._build_tabs()
        self._build_status_bar()

    def _configure_styles(self):
        """Configure modern custom TTK styles."""
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Global settings
        self.style.configure(".", background=THEME["bg_dark"], foreground=THEME["text_primary"], font=(FONT_FAMILY, 10))

        # Notebook tabs
        self.style.configure(
            "TNotebook",
            background=THEME["bg_dark"],
            borderwidth=0,
            tabmargins=[10, 5, 10, 0]
        )
        self.style.configure(
            "TNotebook.Tab",
            background=THEME["bg_card"],
            foreground=THEME["text_secondary"],
            font=(FONT_FAMILY, 10, "bold"),
            padding=[20, 10],
            borderwidth=0
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", THEME["accent_primary"]), ("active", THEME["bg_card_alt"])],
            foreground=[("selected", "#000000"), ("active", THEME["text_primary"])]
        )

        # Buttons
        self.style.configure(
            "Primary.TButton",
            background=THEME["accent_primary"],
            foreground="#000000",
            font=(FONT_FAMILY, 10, "bold"),
            padding=[14, 8],
            borderwidth=0,
            relief="flat"
        )
        self.style.map(
            "Primary.TButton",
            background=[("active", THEME["accent_hover"]), ("disabled", THEME["bg_card_alt"])],
            foreground=[("disabled", THEME["text_secondary"])]
        )

        self.style.configure(
            "Secondary.TButton",
            background=THEME["bg_card_alt"],
            foreground=THEME["text_primary"],
            font=(FONT_FAMILY, 9),
            padding=[10, 6],
            borderwidth=0,
            relief="flat"
        )
        self.style.map(
            "Secondary.TButton",
            background=[("active", "#475569"), ("disabled", THEME["bg_card"])]
        )

        self.style.configure(
            "AccentGreen.TButton",
            background=THEME["accent_green"],
            foreground="#000000",
            font=(FONT_FAMILY, 10, "bold"),
            padding=[14, 8],
            borderwidth=0
        )
        self.style.map(
            "AccentGreen.TButton",
            background=[("active", "#059669")]
        )

        # Progressbar
        self.style.configure(
            "Horizontal.TProgressbar",
            troughcolor=THEME["bg_card"],
            background=THEME["accent_primary"],
            bordercolor=THEME["border"],
            thickness=6
        )

        # Checkbutton
        self.style.configure(
            "TCheckbutton",
            background=THEME["bg_card"],
            foreground=THEME["text_primary"],
            font=(FONT_FAMILY, 10)
        )
        self.style.map(
            "TCheckbutton",
            background=[("active", THEME["bg_card"])],
            foreground=[("active", THEME["accent_primary"])]
        )

    def _build_header(self):
        """Construct the top application header."""
        header_frame = tk.Frame(self, bg=THEME["bg_card"], height=70, padx=20, pady=12)
        header_frame.pack(fill="x", side="top")

        title_box = tk.Frame(header_frame, bg=THEME["bg_card"])
        title_box.pack(side="left")

        title_label = tk.Label(
            title_box,
            text="🔒 SECRETS WITHIN PIXELS",
            font=(FONT_FAMILY, 16, "bold"),
            fg=THEME["accent_primary"],
            bg=THEME["bg_card"]
        )
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(
            title_box,
            text="The Art & Science of LSB Steganography with Password-Authenticated Encryption",
            font=(FONT_FAMILY, 9),
            fg=THEME["text_secondary"],
            bg=THEME["bg_card"]
        )
        subtitle_label.pack(anchor="w")

        # Security specs badge on the right
        badge_frame = tk.Frame(header_frame, bg=THEME["bg_card_alt"], padx=10, pady=4)
        badge_frame.pack(side="right")
        badge_text = tk.Label(
            badge_frame,
            text="AES-Fernet (PBKDF2) + RGB LSB Lossless",
            font=(FONT_MONO, 8, "bold"),
            fg=THEME["accent_green"],
            bg=THEME["bg_card_alt"]
        )
        badge_text.pack()

    def _build_tabs(self):
        """Construct the main notebook tabs."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=10)

        # Tab 1: Hide Secret
        self.tab_hide = tk.Frame(self.notebook, bg=THEME["bg_dark"])
        self.notebook.add(self.tab_hide, text="  🛡️ Hide Secret (Encode)  ")
        self._build_hide_tab(self.tab_hide)

        # Tab 2: Extract Secret
        self.tab_extract = tk.Frame(self.notebook, bg=THEME["bg_dark"])
        self.notebook.add(self.tab_extract, text="  🔍 Extract Secret (Decode)  ")
        self._build_extract_tab(self.tab_extract)

        # Tab 3: Steganography Guide
        self.tab_guide = tk.Frame(self.notebook, bg=THEME["bg_dark"])
        self.notebook.add(self.tab_guide, text="  📖 Steganography & Crypto Guide  ")
        self._build_guide_tab(self.tab_guide)

    def _build_status_bar(self):
        """Construct the bottom status bar."""
        self.status_frame = tk.Frame(self, bg=THEME["bg_card"], height=28, padx=15, pady=4)
        self.status_frame.pack(fill="x", side="bottom")

        self.status_label = tk.Label(
            self.status_frame,
            text="Ready. Select a cover image to begin hiding secrets, or load a stego-image to extract.",
            font=(FONT_FAMILY, 9),
            fg=THEME["text_secondary"],
            bg=THEME["bg_card"]
        )
        self.status_label.pack(side="left")

        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            mode="indeterminate",
            style="Horizontal.TProgressbar",
            length=180
        )
        # Not packed initially, shown only during background operations

    def set_status(self, text: str, is_error: bool = False, is_success: bool = False):
        """Thread-safe status bar update."""
        def _update():
            color = THEME["text_secondary"]
            if is_error:
                color = THEME["accent_red"]
            elif is_success:
                color = THEME["accent_green"]
            self.status_label.config(text=text, fg=color)
        self.after(0, _update)

    def show_progress(self, show: bool = True):
        """Show or hide the indeterminate progress indicator."""
        def _toggle():
            if show:
                self.progress_bar.pack(side="right", padx=10)
                self.progress_bar.start(10)
            else:
                self.progress_bar.stop()
                self.progress_bar.pack_forget()
        self.after(0, _toggle)

    # =========================================================================
    # TAB 1: HIDE SECRET (ENCODE)
    # =========================================================================
    def _build_hide_tab(self, parent: tk.Frame):
        container = tk.Frame(parent, bg=THEME["bg_dark"], padx=15, pady=10)
        container.pack(fill="both", expand=True)

        # Top section: Image Selection & Thumbnail
        img_section = tk.LabelFrame(
            container,
            text=" 1. Cover Image Selection ",
            font=(FONT_FAMILY, 10, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["accent_primary"],
            padx=12,
            pady=10,
            relief="solid",
            bd=1
        )
        img_section.pack(fill="x", pady=(0, 10))

        # Browse row
        browse_row = tk.Frame(img_section, bg=THEME["bg_card"])
        browse_row.pack(fill="x", pady=(0, 8))

        self.hide_path_entry = tk.Entry(
            browse_row,
            font=(FONT_FAMILY, 9),
            bg=THEME["input_bg"],
            fg=THEME["input_fg"],
            insertbackground=THEME["input_fg"],
            relief="flat",
            bd=5
        )
        self.hide_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ttk.Button(
            browse_row,
            text="Browse Image...",
            style="Primary.TButton",
            command=self._on_browse_cover_image
        )
        browse_btn.pack(side="right")

        # Info & Preview Box
        preview_box = tk.Frame(img_section, bg=THEME["bg_card"])
        preview_box.pack(fill="x")

        # Thumbnail canvas
        self.hide_thumb_label = tk.Label(
            preview_box,
            text="No Image Loaded\n(Thumbnail Preview)",
            font=(FONT_FAMILY, 8),
            bg=THEME["bg_card_alt"],
            fg=THEME["text_secondary"],
            width=24,
            height=6,
            relief="groove"
        )
        self.hide_thumb_label.pack(side="left", padx=(0, 15))

        # Image Metadata & Capacity
        self.hide_meta_label = tk.Label(
            preview_box,
            text="Dimensions: N/A\nFormat / Mode: N/A\nTotal Pixel Capacity: 0 bytes (0 characters)\nRecommended Format: PNG (Lossless)",
            font=(FONT_FAMILY, 9),
            justify="left",
            bg=THEME["bg_card"],
            fg=THEME["text_secondary"]
        )
        self.hide_meta_label.pack(side="left", fill="both", expand=True)

        # Middle Section: Secret Message Input
        msg_section = tk.LabelFrame(
            container,
            text=" 2. Secret Message Payload ",
            font=(FONT_FAMILY, 10, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["accent_primary"],
            padx=12,
            pady=10,
            relief="solid",
            bd=1
        )
        msg_section.pack(fill="both", expand=True, pady=(0, 10))

        # Text input area
        text_frame = tk.Frame(msg_section, bg=THEME["bg_card"])
        text_frame.pack(fill="both", expand=True)

        self.hide_text = tk.Text(
            text_frame,
            font=(FONT_FAMILY, 10),
            bg=THEME["input_bg"],
            fg=THEME["input_fg"],
            insertbackground=THEME["input_fg"],
            relief="flat",
            wrap="word",
            height=7,
            bd=5
        )
        self.hide_text.pack(side="left", fill="both", expand=True)
        self.hide_text.bind("<KeyRelease>", self._update_hide_capacity_bar)

        text_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.hide_text.yview)
        text_scroll.pack(side="right", fill="y")
        self.hide_text.config(yscrollcommand=text_scroll.set)

        # Real-time Capacity / Character Counter
        count_bar = tk.Frame(msg_section, bg=THEME["bg_card"])
        count_bar.pack(fill="x", pady=(6, 0))

        self.hide_count_label = tk.Label(
            count_bar,
            text="Payload: 0 characters | Available: 0 | Capacity Used: 0.0%",
            font=(FONT_FAMILY, 9),
            bg=THEME["bg_card"],
            fg=THEME["text_secondary"]
        )
        self.hide_count_label.pack(side="left")

        # Bottom Section: Security & Action
        action_section = tk.LabelFrame(
            container,
            text=" 3. Encryption & Processing ",
            font=(FONT_FAMILY, 10, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["accent_primary"],
            padx=12,
            pady=10,
            relief="solid",
            bd=1
        )
        action_section.pack(fill="x")

        # Password Options
        pass_row = tk.Frame(action_section, bg=THEME["bg_card"])
        pass_row.pack(fill="x", pady=(0, 8))

        self.hide_encrypt_var = tk.BooleanVar(value=False)
        self.hide_encrypt_check = ttk.Checkbutton(
            pass_row,
            text="Encrypt secret with password (AES-Fernet + PBKDF2)",
            variable=self.hide_encrypt_var,
            command=self._toggle_hide_password_field
        )
        self.hide_encrypt_check.pack(side="left")

        self.hide_pass_entry = tk.Entry(
            pass_row,
            font=(FONT_FAMILY, 9),
            bg=THEME["input_bg"],
            fg=THEME["input_fg"],
            insertbackground=THEME["input_fg"],
            show="*",
            state="disabled",
            relief="flat",
            bd=4,
            width=26
        )
        self.hide_pass_entry.pack(side="left", padx=10)

        self.hide_show_pass_btn = ttk.Button(
            pass_row,
            text="👁️ Show",
            style="Secondary.TButton",
            command=lambda: self._toggle_password_visibility(self.hide_pass_entry, self.hide_show_pass_btn)
        )
        self.hide_show_pass_btn.pack(side="left")

        # Encode and Save Button
        btn_row = tk.Frame(action_section, bg=THEME["bg_card"])
        btn_row.pack(fill="x", pady=(4, 0))

        self.encode_btn = ttk.Button(
            btn_row,
            text="⚡ Encode Secret & Save PNG Image...",
            style="AccentGreen.TButton",
            command=self._start_encode_thread
        )
        self.encode_btn.pack(side="right")

    def _toggle_hide_password_field(self):
        """Enable or disable the password entry based on checkbox."""
        if self.hide_encrypt_var.get():
            self.hide_pass_entry.config(state="normal")
            self.hide_pass_entry.focus()
        else:
            self.hide_pass_entry.config(state="disabled")

    def _toggle_password_visibility(self, entry_widget: tk.Entry, button_widget: ttk.Button):
        """Toggle mask character for password entries."""
        if entry_widget.cget("show") == "*":
            entry_widget.config(show="")
            button_widget.config(text="🙈 Hide")
        else:
            entry_widget.config(show="*")
            button_widget.config(text="👁️ Show")

    def _on_browse_cover_image(self):
        """Open file dialog to choose cover image and compute capacity."""
        file_path = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[
                ("Supported Images", "*.png;*.jpg;*.jpeg;*.bmp;*.webp;*.tiff"),
                ("PNG Lossless (*.png)", "*.png"),
                ("All Files (*.*)", "*.*")
            ]
        )
        if not file_path:
            return

        try:
            img = Image.open(file_path)
            self.encode_image_path = file_path
            self.encode_image_obj = img
            self.hide_path_entry.delete(0, tk.END)
            self.hide_path_entry.insert(0, file_path)

            # Check format and warn if JPEG
            ext = os.path.splitext(file_path)[1].lower()
            format_warning = ""
            if ext in (".jpg", ".jpeg"):
                format_warning = " ⚠️ Note: Source is JPEG. Output will strictly be saved as lossless PNG."

            # Calculate capacity
            cap = stego.get_image_capacity(img)
            self.encode_capacity_info = cap

            meta_text = (
                f"Dimensions: {cap['width']} × {cap['height']} px  ({cap['total_pixels']:,} pixels)\n"
                f"Mode: {img.mode}  |  Format: {img.format or ext.upper()}{format_warning}\n"
                f"Max Storage Capacity: {cap['usable_bytes']:,} bytes (~{cap['usable_ascii_chars']:,} ASCII characters)\n"
                f"LSB Channels: Red, Green, Blue (3 bits embedded per pixel)"
            )
            self.hide_meta_label.config(text=meta_text, fg=THEME["text_primary"])

            # Generate thumbnail preview
            thumb = img.copy()
            thumb.thumbnail((160, 110))
            self.encode_thumbnail_photo = ImageTk.PhotoImage(thumb)
            self.hide_thumb_label.config(image=self.encode_thumbnail_photo, text="", width=160, height=110)

            self._update_hide_capacity_bar()
            self.set_status(f"Cover image loaded: {os.path.basename(file_path)} ({cap['usable_bytes']:,} bytes capacity).")

        except Exception as e:
            messagebox.showerror("Image Load Error", f"Unable to load image file:\n{e}")
            self.set_status(f"Error loading image: {e}", is_error=True)

    def _update_hide_capacity_bar(self, event=None):
        """Update live character count and capacity percentage indicator."""
        if not self.encode_capacity_info:
            return

        text = self.hide_text.get("1.0", "end-1c")
        char_count = len(text)
        byte_count = len(text.encode("utf-8"))
        usable_bytes = self.encode_capacity_info.get("usable_bytes", 0)

        if usable_bytes > 0:
            pct = (byte_count / usable_bytes) * 100
        else:
            pct = 100.0

        if pct <= 75.0:
            color = THEME["accent_green"]
            status_desc = "Safe"
        elif pct <= 100.0:
            color = THEME["accent_amber"]
            status_desc = "Approaching Limit"
        else:
            color = THEME["accent_red"]
            status_desc = "CAPACITY EXCEEDED!"

        self.hide_count_label.config(
            text=f"Payload: {char_count:,} chars ({byte_count:,} bytes) | Usable Limit: {usable_bytes:,} bytes | Used: {pct:.2f}% [{status_desc}]",
            fg=color
        )

    def _start_encode_thread(self):
        """Validate inputs and launch encoding in a background thread."""
        if not self.encode_image_obj:
            messagebox.showwarning("Missing Image", "Please select a cover image first.")
            return

        message = self.hide_text.get("1.0", "end-1c").strip()
        if not message:
            messagebox.showwarning("Empty Message", "Please type or paste a secret message to hide.")
            return

        # Handle encryption if selected
        is_encrypted = self.hide_encrypt_var.get()
        password = self.hide_pass_entry.get().strip() if is_encrypted else ""

        if is_encrypted and not password:
            messagebox.showwarning("Password Required", "Password encryption is enabled. Please enter an encryption password.")
            self.hide_pass_entry.focus()
            return

        # Pre-check capacity before file dialog
        payload_to_test = message
        if is_encrypted:
            # Approximate encrypted length: ~1.4x + base64 overhead
            payload_to_test = crypto.encrypt_message(message, password)

        payload_bytes_len = len((payload_to_test + stego.DEFAULT_DELIMITER).encode("utf-8"))
        usable_bytes = self.encode_capacity_info.get("usable_bytes", 0)

        if payload_bytes_len > usable_bytes:
            messagebox.showerror(
                "Capacity Exceeded",
                f"The secret payload is too large for the selected image!\n\n"
                f"Required Capacity: {payload_bytes_len:,} bytes\n"
                f"Available Capacity: {usable_bytes:,} bytes\n"
                f"Deficit: {payload_bytes_len - usable_bytes:,} bytes\n\n"
                f"Please choose a larger cover image or shorten your secret message."
            )
            return

        # Select output file path (Strictly enforce PNG)
        default_dir = os.path.dirname(self.encode_image_path) if self.encode_image_path else ""
        output_file = filedialog.asksaveasfilename(
            title="Save Stego-Image As (Must be PNG)",
            initialdir=default_dir,
            initialfile="stego_secret.png",
            defaultextension=".png",
            filetypes=[("Lossless PNG Image (*.png)", "*.png")]
        )
        if not output_file:
            return

        # Strictly verify .png extension
        if not output_file.lower().endswith(".png"):
            messagebox.showerror(
                "Invalid Format",
                "Stego-images MUST be saved with the .png extension to prevent lossy compression from destroying hidden data."
            )
            return

        # Disable UI elements during processing
        self.encode_btn.config(state="disabled")
        self.show_progress(True)
        self.set_status("Embedding secret payload into image pixels...")

        def _worker():
            try:
                final_payload = message
                if is_encrypted:
                    final_payload = crypto.encrypt_message(message, password)

                stego_img = stego.encode_lsb(self.encode_image_obj, final_payload)
                stego.save_stego_image(stego_img, output_file)

                def _on_success():
                    self.show_progress(False)
                    self.encode_btn.config(state="normal")
                    self.set_status(f"Success! Stego-image saved to: {output_file}", is_success=True)
                    messagebox.showinfo(
                        "Steganography Complete",
                        f"Secret message successfully embedded into pixels!\n\n"
                        f"Output File: {output_file}\n"
                        f"Encryption: {'AES-Fernet (PBKDF2 Password Protected)' if is_encrypted else 'Plaintext (No Encryption)'}\n"
                        f"Format: Lossless PNG"
                    )

                self.after(0, _on_success)

            except Exception as e:
                def _on_error(err=e):
                    self.show_progress(False)
                    self.encode_btn.config(state="normal")
                    self.set_status(f"Encoding failed: {err}", is_error=True)
                    messagebox.showerror("Encoding Error", f"An error occurred during steganography encoding:\n{err}")

                self.after(0, _on_error)

        threading.Thread(target=_worker, daemon=True).start()

    # =========================================================================
    # TAB 2: EXTRACT SECRET (DECODE)
    # =========================================================================
    def _build_extract_tab(self, parent: tk.Frame):
        container = tk.Frame(parent, bg=THEME["bg_dark"], padx=15, pady=10)
        container.pack(fill="both", expand=True)

        # Top section: Stego-Image Selection
        img_section = tk.LabelFrame(
            container,
            text=" 1. Stego-Image Selection ",
            font=(FONT_FAMILY, 10, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["accent_primary"],
            padx=12,
            pady=10,
            relief="solid",
            bd=1
        )
        img_section.pack(fill="x", pady=(0, 10))

        browse_row = tk.Frame(img_section, bg=THEME["bg_card"])
        browse_row.pack(fill="x", pady=(0, 8))

        self.decode_path_entry = tk.Entry(
            browse_row,
            font=(FONT_FAMILY, 9),
            bg=THEME["input_bg"],
            fg=THEME["input_fg"],
            insertbackground=THEME["input_fg"],
            relief="flat",
            bd=5
        )
        self.decode_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ttk.Button(
            browse_row,
            text="Browse Stego-Image...",
            style="Primary.TButton",
            command=self._on_browse_stego_image
        )
        browse_btn.pack(side="right")

        # Preview & Info Box
        preview_box = tk.Frame(img_section, bg=THEME["bg_card"])
        preview_box.pack(fill="x")

        self.decode_thumb_label = tk.Label(
            preview_box,
            text="No Image Loaded\n(Thumbnail Preview)",
            font=(FONT_FAMILY, 8),
            bg=THEME["bg_card_alt"],
            fg=THEME["text_secondary"],
            width=24,
            height=6,
            relief="groove"
        )
        self.decode_thumb_label.pack(side="left", padx=(0, 15))

        self.decode_meta_label = tk.Label(
            preview_box,
            text="Dimensions: N/A\nFormat / Mode: N/A\nStatus: Waiting for stego-image file...",
            font=(FONT_FAMILY, 9),
            justify="left",
            bg=THEME["bg_card"],
            fg=THEME["text_secondary"]
        )
        self.decode_meta_label.pack(side="left", fill="both", expand=True)

        # Middle Section: Authentication & Trigger
        auth_section = tk.LabelFrame(
            container,
            text=" 2. Authentication & Extraction ",
            font=(FONT_FAMILY, 10, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["accent_primary"],
            padx=12,
            pady=10,
            relief="solid",
            bd=1
        )
        auth_section.pack(fill="x", pady=(0, 10))

        auth_row = tk.Frame(auth_section, bg=THEME["bg_card"])
        auth_row.pack(fill="x")

        pass_label = tk.Label(
            auth_row,
            text="Password (if encrypted):",
            font=(FONT_FAMILY, 9),
            bg=THEME["bg_card"],
            fg=THEME["text_primary"]
        )
        pass_label.pack(side="left", padx=(0, 8))

        self.decode_pass_entry = tk.Entry(
            auth_row,
            font=(FONT_FAMILY, 9),
            bg=THEME["input_bg"],
            fg=THEME["input_fg"],
            insertbackground=THEME["input_fg"],
            show="*",
            relief="flat",
            bd=4,
            width=24
        )
        self.decode_pass_entry.pack(side="left", padx=(0, 8))

        self.decode_show_pass_btn = ttk.Button(
            auth_row,
            text="👁️ Show",
            style="Secondary.TButton",
            command=lambda: self._toggle_password_visibility(self.decode_pass_entry, self.decode_show_pass_btn)
        )
        self.decode_show_pass_btn.pack(side="left", padx=(0, 15))

        self.decode_btn = ttk.Button(
            auth_row,
            text="🔓 Extract Hidden Secret",
            style="Primary.TButton",
            command=self._start_decode_thread
        )
        self.decode_btn.pack(side="right")

        # Bottom Section: Revealed Secret Message
        result_section = tk.LabelFrame(
            container,
            text=" 3. Revealed Secret Message ",
            font=(FONT_FAMILY, 10, "bold"),
            bg=THEME["bg_card"],
            fg=THEME["accent_green"],
            padx=12,
            pady=10,
            relief="solid",
            bd=1
        )
        result_section.pack(fill="both", expand=True)

        # Output text area
        out_frame = tk.Frame(result_section, bg=THEME["bg_card"])
        out_frame.pack(fill="both", expand=True)

        self.decode_text = tk.Text(
            out_frame,
            font=(FONT_FAMILY, 10),
            bg=THEME["input_bg"],
            fg=THEME["input_fg"],
            insertbackground=THEME["input_fg"],
            relief="flat",
            wrap="word",
            state="disabled",
            bd=5
        )
        self.decode_text.pack(side="left", fill="both", expand=True)

        out_scroll = ttk.Scrollbar(out_frame, orient="vertical", command=self.decode_text.yview)
        out_scroll.pack(side="right", fill="y")
        self.decode_text.config(yscrollcommand=out_scroll.set)

        # Action row below output
        action_bar = tk.Frame(result_section, bg=THEME["bg_card"])
        action_bar.pack(fill="x", pady=(8, 0))

        self.decode_badge_label = tk.Label(
            action_bar,
            text="No message extracted yet.",
            font=(FONT_FAMILY, 9),
            bg=THEME["bg_card"],
            fg=THEME["text_secondary"]
        )
        self.decode_badge_label.pack(side="left")

        self.copy_btn = ttk.Button(
            action_bar,
            text="📋 Copy to Clipboard",
            style="Secondary.TButton",
            state="disabled",
            command=self._copy_extracted_text
        )
        self.copy_btn.pack(side="right", padx=(8, 0))

        self.save_txt_btn = ttk.Button(
            action_bar,
            text="💾 Save to .txt...",
            style="Secondary.TButton",
            state="disabled",
            command=self._save_extracted_to_file
        )
        self.save_txt_btn.pack(side="right")

    def _on_browse_stego_image(self):
        """Browse and load the stego-image file."""
        file_path = filedialog.askopenfilename(
            title="Select Stego-Image",
            filetypes=[
                ("PNG Lossless (*.png)", "*.png"),
                ("All Images", "*.png;*.bmp;*.webp;*.jpg;*.jpeg"),
                ("All Files (*.*)", "*.*")
            ]
        )
        if not file_path:
            return

        try:
            img = Image.open(file_path)
            self.decode_image_path = file_path
            self.decode_image_obj = img
            self.decode_path_entry.delete(0, tk.END)
            self.decode_path_entry.insert(0, file_path)

            ext = os.path.splitext(file_path)[1].lower()
            warning = ""
            if ext in (".jpg", ".jpeg"):
                warning = "\n⚠️ Warning: JPEG format detected. Lossy compression likely corrupted any LSB data!"

            meta_text = (
                f"Dimensions: {img.width} × {img.height} px\n"
                f"Mode: {img.mode}  |  Format: {img.format or ext.upper()}{warning}\n"
                f"Ready for LSB extraction."
            )
            self.decode_meta_label.config(text=meta_text, fg=THEME["text_primary"])

            # Thumbnail preview
            thumb = img.copy()
            thumb.thumbnail((160, 110))
            self.decode_thumbnail_photo = ImageTk.PhotoImage(thumb)
            self.decode_thumb_label.config(image=self.decode_thumbnail_photo, text="", width=160, height=110)

            self.set_status(f"Stego-image loaded: {os.path.basename(file_path)}")

        except Exception as e:
            messagebox.showerror("Image Load Error", f"Unable to open image file:\n{e}")
            self.set_status(f"Error loading image: {e}", is_error=True)

    def _start_decode_thread(self):
        """Launch secret message extraction in a background thread."""
        if not self.decode_image_obj:
            messagebox.showwarning("Missing Image", "Please select a stego-image to extract secrets from.")
            return

        password = self.decode_pass_entry.get().strip()

        # UI state
        self.decode_btn.config(state="disabled")
        self.show_progress(True)
        self.set_status("Scanning image pixels and extracting LSB stream...")

        def _worker():
            try:
                # Step 1: Extract raw payload from LSBs
                raw_payload = stego.decode_lsb(self.decode_image_obj)

                # Step 2: Determine if payload is encrypted
                if crypto.is_encrypted(raw_payload):
                    if not password:
                        # User needs to provide password
                        def _prompt_password():
                            self.show_progress(False)
                            self.decode_btn.config(state="normal")
                            self.set_status("Password required: secret is encrypted.", is_error=True)
                            messagebox.showwarning(
                                "Password Required",
                                "The hidden message inside this image was encrypted with a password!\n\n"
                                "Please enter the secret password in the field above and click 'Extract Hidden Secret' again."
                            )
                            self.decode_pass_entry.focus()
                        self.after(0, _prompt_password)
                        return

                    # Attempt decryption
                    try:
                        decrypted_text = crypto.decrypt_message(raw_payload, password)
                        final_message = decrypted_text
                        status_note = "Decrypted successfully via AES-Fernet (PBKDF2 authenticated)"
                        badge_color = THEME["accent_green"]
                    except crypto.InvalidPasswordError:
                        def _wrong_pass():
                            self.show_progress(False)
                            self.decode_btn.config(state="normal")
                            self.set_status("Decryption failed: Incorrect password.", is_error=True)
                            messagebox.showerror(
                                "Decryption Failed",
                                "Incorrect password! Could not decrypt the hidden secret.\n\n"
                                "Please verify the password and try again."
                            )
                        self.after(0, _wrong_pass)
                        return
                else:
                    final_message = raw_payload
                    status_note = "Plaintext message extracted (No encryption)"
                    badge_color = THEME["accent_primary"]

                def _on_success():
                    self.show_progress(False)
                    self.decode_btn.config(state="normal")
                    self._set_extracted_text(final_message)
                    self.decode_badge_label.config(
                        text=f"Status: {status_note} | {len(final_message):,} characters",
                        fg=badge_color
                    )
                    self.copy_btn.config(state="normal")
                    self.save_txt_btn.config(state="normal")
                    self.set_status("Extraction complete!", is_success=True)

                self.after(0, _on_success)

            except stego.NoHiddenMessageError as e:
                def _on_no_msg():
                    self.show_progress(False)
                    self.decode_btn.config(state="normal")
                    self.set_status("No hidden message found in this image.", is_error=True)
                    messagebox.showinfo("No Secret Found", str(e))
                self.after(0, _on_no_msg)

            except Exception as e:
                def _on_error(err=e):
                    self.show_progress(False)
                    self.decode_btn.config(state="normal")
                    self.set_status(f"Extraction error: {err}", is_error=True)
                    messagebox.showerror("Extraction Error", f"Failed to extract hidden message:\n{err}")
                self.after(0, _on_error)

        threading.Thread(target=_worker, daemon=True).start()

    def _set_extracted_text(self, text: str):
        """Populate the read-only output text widget."""
        self.decode_text.config(state="normal")
        self.decode_text.delete("1.0", tk.END)
        self.decode_text.insert("1.0", text)
        self.decode_text.config(state="disabled")

    def _copy_extracted_text(self):
        """Copy extracted message to system clipboard."""
        text = self.decode_text.get("1.0", "end-1c")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.set_status("Secret message copied to clipboard!", is_success=True)
            self.copy_btn.config(text="✓ Copied!")
            self.after(2000, lambda: self.copy_btn.config(text="📋 Copy to Clipboard"))

    def _save_extracted_to_file(self):
        """Export extracted message to a text file."""
        text = self.decode_text.get("1.0", "end-1c")
        if not text:
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Extracted Message",
            defaultextension=".txt",
            filetypes=[("Text File (*.txt)", "*.txt"), ("All Files (*.*)", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.set_status(f"Message exported to: {file_path}", is_success=True)
            messagebox.showinfo("Saved", f"Secret message saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save text file:\n{e}")

    # =========================================================================
    # TAB 3: GUIDE & CYBERSECURITY INSPECTOR
    # =========================================================================
    def _build_guide_tab(self, parent: tk.Frame):
        container = tk.Frame(parent, bg=THEME["bg_dark"], padx=20, pady=15)
        container.pack(fill="both", expand=True)

        guide_text = tk.Text(
            container,
            font=(FONT_FAMILY, 10),
            bg=THEME["bg_card"],
            fg=THEME["text_primary"],
            relief="flat",
            wrap="word",
            padx=16,
            pady=16,
            bd=1
        )
        guide_text.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(container, orient="vertical", command=guide_text.yview)
        scroll.pack(side="right", fill="y")
        guide_text.config(yscrollcommand=scroll.set)

        # Content for Guide
        content = """SECRETS WITHIN PIXELS: TECHNICAL SPECIFICATION & GUIDE
=====================================================================

1. The Mechanics of LSB (Least Significant Bit) Steganography
--------------------------------------------------------------
Digital images are grids of pixels. In standard 24-bit TrueColor images, each pixel consists of 3 color channels:
- Red   (8 bits: 0 - 255)
- Green (8 bits: 0 - 255)
- Blue  (8 bits: 0 - 255)

The Least Significant Bit (Bit 0) contributes only 2^0 = 1 unit of intensity out of 255 (~0.39% change).
Because human vision cannot differentiate between RGB(200, 150, 100) and RGB(201, 150, 100), we can replace Bit 0 in each channel with secret data bits without noticeable visual degradation.

Bitwise Math:
  - Clear Bit 0:   pixel_value & ~1    (e.g., 10101111 & 11111110 = 10101110)
  - Embed Bit (b): (pixel_value & ~1) | b
  - Extract Bit:   pixel_value & 1

2. Storage Capacity Formula
----------------------------
  Total Usable Bits  = Width × Height × 3 channels
  Total Usable Bytes = Total Bits // 8
  
Example:
  - A 1920 × 1080 Full HD image:
    1920 × 1080 = 2,073,600 pixels
    2,073,600 × 3 = 6,220,800 bits = 777,600 bytes (~759 KB of raw text).
    This can store an entire novel inside a single photo!

3. Lossless PNG vs. Lossy JPEG (Format Enforcement)
----------------------------------------------------
  - PNG uses Deflate (LZ77 + Huffman coding) which is 100% LOSSLESS. Every pixel remains bit-identical.
  - JPEG uses Discrete Cosine Transform (DCT) and lossy quantization. It permanently averages high-frequency pixel variations, destroying LSB data instantly.
  - Therefore, Stego-images MUST ALWAYS be saved as PNG.

4. Password Protection Architecture (Defense-in-Depth)
-------------------------------------------------------
Steganography provides "Security through Obscurity" (hiding the existence of communication).
Cryptography provides "Confidentiality" (protecting content if discovered).
Combining both yields defense-in-depth:
  1. Key Derivation: PBKDF2-HMAC-SHA256 with 480,000 iterations and a 16-byte random salt.
  2. Authenticated Encryption: Fernet (AES-128 in CBC mode + HMAC-SHA256).
  3. Tamper Resistance: Any bit corruption or wrong password immediately fails HMAC verification, preventing partial decryptions.
"""
        guide_text.insert("1.0", content)
        guide_text.config(state="disabled")


def main():
    app = SteganographyApp()
    app.mainloop()


if __name__ == "__main__":
    main()
