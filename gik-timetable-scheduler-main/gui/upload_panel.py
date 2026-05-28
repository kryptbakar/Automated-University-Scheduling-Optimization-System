"""
upload_panel.py
Single-action upload screen.

Design: Refined minimalism. One clear flow — select file, click generate.
No options, no info panels, no decorative elements.
"""

import threading
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk


class UploadPanel(ctk.CTkFrame):

    def __init__(self, master, colors: dict, fonts: dict, on_generate, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.C = colors
        self.F = fonts
        self.on_generate = on_generate
        self._path: Path | None = None
        self._registration_path: Path | None = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)   # vertical centering
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # Centered container — gives the content breathing room
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=1, column=0, sticky="n", pady=(48, 0))
        center.columnconfigure(0, weight=1)

        # ── Overline label (small uppercase marker) ───────────────────────────
        ctk.CTkLabel(
            center,
            text="TIMETABLE GENERATOR",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=self.C["accent"],
        ).grid(row=0, column=0, pady=(0, 14))

        # ── Display headline ──────────────────────────────────────────────────
        ctk.CTkLabel(
            center,
            text="Generate the semester schedule.",
            font=ctk.CTkFont(family="Georgia", size=34, weight="normal"),
            text_color=self.C["text_primary"],
        ).grid(row=1, column=0)

        # ── Subtitle ──────────────────────────────────────────────────────────
        ctk.CTkLabel(
            center,
            text="Upload your offered courses file. One click to produce a clash-free timetable.",
            font=self.F["body"],
            text_color=self.C["text_secondary"],
            wraplength=600,
        ).grid(row=2, column=0, pady=(12, 44))

        # ── File drop area (clickable, minimal) ───────────────────────────────
        self._drop = ctk.CTkFrame(
            center,
            fg_color=self.C["bg_surface"],
            corner_radius=12,
            border_width=1,
            border_color=self.C["border"],
            width=640, height=140,
        )
        self._drop.grid(row=3, column=0, sticky="ew", padx=40)
        self._drop.grid_propagate(False)
        self._drop.columnconfigure(0, weight=1)
        self._drop.rowconfigure(0, weight=1)

        drop_inner = ctk.CTkFrame(self._drop, fg_color="transparent")
        drop_inner.grid(row=0, column=0)

        self._drop_icon = ctk.CTkLabel(
            drop_inner,
            text="↑",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="normal"),
            text_color=self.C["text_muted"],
        )
        self._drop_icon.pack()

        self._drop_text = ctk.CTkLabel(
            drop_inner,
            text="Click to choose courses file",
            font=self.F["body"],
            text_color=self.C["text_secondary"],
        )
        self._drop_text.pack(pady=(6, 2))

        self._drop_hint = ctk.CTkLabel(
            drop_inner,
            text=".xlsx · Code · Section · Title · CHs · Instructor",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.C["text_muted"],
        )
        self._drop_hint.pack()

        # Make the whole drop area clickable
        for w in (self._drop, drop_inner, self._drop_icon, self._drop_text, self._drop_hint):
            w.bind("<Button-1>", lambda _: self._on_upload_click())
            w.bind("<Enter>",    lambda _: self._hover_in())
            w.bind("<Leave>",    lambda _: self._hover_out())
            try:
                w.configure(cursor="hand2")
            except Exception:
                pass

        # ── Generate button ───────────────────────────────────────────────────
        self._generate_btn = ctk.CTkButton(
            center,
            text="Generate Timetable",
            font=self.F["button"],
            corner_radius=8,
            height=42,
            command=self._on_generate_click,
            state="disabled",
        )
        self._generate_btn.grid(row=4, column=0, pady=(32, 0))

        # ── Registration file button ────────────────────────────────────────
        self._reg_btn = ctk.CTkButton(
            center,
            text="Upload Student Registrations (Optional)",
            font=self.F["button"],
            corner_radius=8,
            height=32,
            command=self._on_reg_upload_click,
            fg_color="transparent",
            border_color=self.C["border"],
            border_width=1,
            hover_color=self.C["bg_surface"],
        )
        self._reg_btn.grid(row=5, column=0, pady=(12, 0))

        # ── Progress label (hidden initially) ─────────────────────────────────
        self._progress_label = ctk.CTkLabel(
            center,
            text="",
            font=self.F["body"],
            text_color=self.C["text_secondary"],
        )
        self._progress_label.grid(row=6, column=0, pady=(24, 0))

    # ── UI Interactions ────────────────────────────────────────────────

    def _hover_in(self, event=None):
        self._drop.configure(border_color=self.C["accent"])

    def _hover_out(self, event=None):
        if not self._path:
            self._drop.configure(border_color=self.C["border"])

    def _on_upload_click(self, event=None):
        path = filedialog.askopenfilename(
            title="Select Offered Courses File",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if not path:
            return
        self._path = Path(path)
        self._drop_text.configure(text=self._path.name)
        self._drop_icon.configure(text="✓")
        self._drop.configure(border_color=self.C["accent"])
        self._generate_btn.configure(state="normal")

    def _on_reg_upload_click(self, event=None):
        path = filedialog.askopenfilename(
            title="Select Student Registration File",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if not path:
            return
        self._registration_path = Path(path)
        self._reg_btn.configure(
            text=f"Registrations: {self._registration_path.name}",
            fg_color=self.C["accent"],
            text_color=self.C["text_inverse"],
        )

    def _on_generate_click(self):
        if not self._path:
            return
        self._generate_btn.configure(state="disabled", text="Generating...")
        self._progress_label.configure(text="Starting...")
        threading.Thread(target=self._run, daemon=True).start()

    def _reset_ui(self):
        self._generate_btn.configure(state="normal", text="Generate Timetable")
        self._progress_label.configure(text="")

    def _show_error(self, message):
        messagebox.showerror("Error", message)
        self._reset_ui()

    # ── Generation ────────────────────────────────────────────────────────────

    def _on_progress(self, assigned: int, total: int):
        pct = int((assigned / max(total, 1)) * 100)
        self.after(0, self._progress_label.configure,
                   {"text": f"Placing {assigned:,} of {total:,} sessions  ·  {pct}%"})

    def _run(self):
        try:
            from src.parser.course_parser import CourseParser
            from src.parser.registration_parser import RegistrationParser
            from src.parser.timetable_parser import TimetableParser
            from src.scheduler.csp_solver import CSPSolver
            from src.scheduler.prerequisite_checker import PrerequisiteChecker

            courses = CourseParser(self._path).parse()
            students, registrations = (
                RegistrationParser(self._registration_path).parse()
                if self._registration_path else ([], [])
            )

            # Warn about prerequisite violations (non-blocking)
            if students and registrations:
                prereq_checker = PrerequisiteChecker(courses, students, registrations)
                prereq_violations = prereq_checker.check()
                if prereq_violations:
                    msg = "\n".join(prereq_violations[:5])
                    if len(prereq_violations) > 5:
                        msg += f"\n...and {len(prereq_violations) - 5} more"
                    self.after(0, messagebox.showwarning,
                               "Prerequisite Violations",
                               f"Found {len(prereq_violations)} violation(s):\n\n{msg}\n\nScheduling will proceed.")

            tt = TimetableParser(None)
            solver = CSPSolver(
                courses, tt,
                students=students,
                registrations=registrations,
                minimize_gaps=True,
                continuous_labs=True,
                time_limit=120.0,
                on_progress=self._on_progress,
            )
            solution = solver.solve()
            report   = solver.report()

            if not solution:
                self.after(0, self._show_error, "Could not place any courses. Check your courses file.")
                return

            self.after(0, self.on_generate, solution, report)

        except Exception as e:
            self.after(0, self._show_error, str(e))
        finally:
            self.after(0, self._reset_ui)