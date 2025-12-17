"""
Artwork Calendar GUI — GitHub-style contribution heatmap for a folder
Features implemented:
1. Hover tooltip (date + count)
2. Click a day to list Art Work Done/modified that day
3. Select folder button (choose any folder)
4. Auto refresh (polling + manual refresh)
5. Smooth animation when redrawing (column-by-column draw)
6. Resizable window + zoom slider with percentage
7. Save calendar as PNG (requires Pillow)
8. Daily/Weekly stats sidebar
9. Full GitHub layout: month labels, weekday labels, legend, year selector

Dependencies: standard library + Pillow (optional, for Save as PNG).
To install Pillow: pip install pillow

How to run: python artwork_calendar.py

Author: Dev Rigan Koijam
"""

import os
import math
import calendar
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import defaultdict
import json

# Optional Pillow import for saving PNGs
try:
    from PIL import Image, ImageDraw, ImageGrab
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# ---------------------------
# Configuration / Defaults
# ---------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FOLDER = SCRIPT_DIR 
REFRESH_INTERVAL_MS = 5000  # auto refresh every 5 seconds
ANIMATION_DELAY_MS = 5      # ms between drawing cells (column animation)
DEFAULT_YEAR_RANGE = 1      # number of years to show (1 = last 365 days)

# Color palettes
LIGHT_PALETTE = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]

WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ---------------------------
# Helper functions
# ---------------------------

def human_date(d: datetime.date):
    return d.strftime('%Y-%m-%d (%a)')


def get_file_dates(folder):
    files_by_date = defaultdict(list)
    if not os.path.exists(folder):
        return files_by_date

    try:
        for entry in os.scandir(folder):
            if entry.is_file() and not entry.name.endswith('.json'):
                ts = entry.stat().st_mtime
                d = datetime.date.fromtimestamp(ts)
                files_by_date[d].append(entry.path)
    except PermissionError:
        pass
    return files_by_date




def contribution_color(palette, count):
    if count == 0:
        return palette[0]
    if count == 1:
        return palette[1]
    if count <= 3:
        return palette[2]
    if count <= 6:
        return palette[3]
    return palette[4]


# ---------------------------
# Main App
# ---------------------------
class ArtworkCalendarApp:
    def __init__(self, root):
        self.root = root
        self.folder = DEFAULT_FOLDER
        self.palette = LIGHT_PALETTE
        self.dark_mode = False
        self.year_range = DEFAULT_YEAR_RANGE
        self.zoom = 1.0
        self.cell_size = 16
        self.box = 12

        # ---- Add these lines ----
        self.tracking_file = os.path.join(self.folder, "tracking.json")
        self.tracking_enabled = False
        self.tracked_files = {}   # filename -> last mtime (float)
        self.file_metadata = {}   # filename -> {"mod_count": int, "history": [mtime1, mtime2, ...]}

        # -------------------------

        # stores mapping from canvas item -> date
        self.rect_to_date = {}
        self.date_to_rects = defaultdict(list)
        self.contributions = defaultdict(int)
        self.files_by_date = defaultdict(list)
        self._stop_poll = False

        self.setup_ui()
        self.load_folder(self.folder)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(REFRESH_INTERVAL_MS, self._auto_rescan)
        
        
    def setup_ui(self):
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=8, pady=6)

        folder_label = ttk.Label(top, text="Folder:")
        folder_label.pack(side=tk.LEFT)

        self.folder_var = tk.StringVar(value=self.folder)
        folder_entry = ttk.Entry(top, textvariable=self.folder_var, width=50)
        folder_entry.pack(side=tk.LEFT, padx=(6, 6))

        choose_btn = ttk.Button(top, text="Choose...", command=self._choose_folder)
        choose_btn.pack(side=tk.LEFT)

        refresh_btn = ttk.Button(top, text="Refresh", command=self._manual_refresh)
        refresh_btn.pack(side=tk.LEFT, padx=(6, 6))

        save_btn = ttk.Button(top, text="Save PNG", command=self._save_png)
        save_btn.pack(side=tk.LEFT)

        self.track_btn = ttk.Button(top, text="Start Tracking", command=self._start_tracking)
        self.track_btn.pack(side=tk.LEFT, padx=(6,6))

        # Year selector
        year_frame = ttk.Frame(top)
        year_frame.pack(side=tk.LEFT, padx=(10,0))
        ttk.Label(year_frame, text="Years:").pack(side=tk.LEFT)
        self.years_var = tk.IntVar(value=self.year_range)
        years_spin = ttk.Spinbox(
            year_frame,
            from_=1,
            to=5,
            width=3,
            textvariable=self.years_var,
            command=self._on_year_change  # <- important
        )

        years_spin.pack(side=tk.LEFT)

        # Zoom slider with percentage
        zoom_frame = ttk.Frame(top)
        zoom_frame.pack(side=tk.RIGHT)
        ttk.Label(zoom_frame, text="Zoom").pack(side=tk.LEFT)
        self.zoom_var = tk.DoubleVar(value=self.zoom)
        zoom_scale = ttk.Scale(zoom_frame, from_=0.5, to=2.0, orient=tk.HORIZONTAL, variable=self.zoom_var, command=self._on_zoom)
        zoom_scale.pack(side=tk.LEFT)
        self.zoom_percent_label = ttk.Label(zoom_frame, text=f"{int(self.zoom*100)}%")
        self.zoom_percent_label.pack(side=tk.LEFT, padx=(4,0))

        content = ttk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True)

        canvas_frame = ttk.Frame(content)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_click)

        self.sidebar = ttk.Frame(content, width=220)  # make sidebar smaller if needed
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=(10,0))




        ttk.Label(self.sidebar, text="Stats", font=(None, 12, "bold")).pack(pady=(6,4))
        self.stats_text = tk.Text(self.sidebar, width=28, height=20, state=tk.DISABLED)
        self.stats_text.pack(padx=1, pady=1)

        self.tooltip = None

        legend_frame = ttk.Frame(self.root)
        legend_frame.pack(fill=tk.X, padx=8, pady=(0,6))
        ttk.Label(legend_frame, text="Legend:").pack(side=tk.LEFT)
        for i, label in enumerate(["0","1","2-3","4-6","7+"]):
            c = contribution_color(self.palette, i if i>0 else 0)
            sw = tk.Canvas(legend_frame, width=18, height=14)
            sw.create_rectangle(0,0,18,14, fill=c, outline="#ccc")
            sw.pack(side=tk.LEFT, padx=4)
            ttk.Label(legend_frame, text=label).pack(side=tk.LEFT, padx=(0,6))

        # Year label above calendar
        self.year_label_canvas = self.canvas.create_text(10, 20, text="", anchor='w', font=(None, 12, 'bold'))

        # --- Charts Section ---
        # Container for charts
        charts_container = ttk.Frame(self.root)
        charts_container.pack(fill=tk.X, padx=8, pady=4)

        # Year selector and Update button at the top
        controls_frame = ttk.Frame(charts_container)
        controls_frame.pack(fill=tk.X, pady=(0,4))

        year_choices = [str(datetime.date.today().year - i) for i in range(5)]
        self.chart_year_var = tk.StringVar(value=year_choices[0])
        ttk.Label(controls_frame, text="Select Year:").pack(side=tk.LEFT)
        ttk.Combobox(controls_frame, textvariable=self.chart_year_var, values=year_choices, width=6, state="readonly").pack(side=tk.LEFT, padx=6)
        ttk.Button(controls_frame, text="Update Charts", command=self._update_charts).pack(side=tk.LEFT, padx=6)
        self.export_charts_btn = ttk.Button(
            controls_frame,
            text="Export Charts",
            command=self._export_charts
        )


        # Charts label below the controls
        charts_label = ttk.Label(charts_container, text="Data Visualization", font=(None, 12, "bold"))
        charts_label.pack(pady=(2,4))

        # Frame for the actual chart canvases
        self.charts_frame = ttk.Frame(charts_container)
        self.charts_frame.pack(fill=tk.X)

        self.chart_canvas_pie = None
        self.chart_canvas_line = None
        self.canvas.bind('<Configure>', lambda e: self._draw_calendar(animate=False))

    # ---------------------------
    # Folder and data handling
    # ---------------------------
    def load_folder(self, folder):
        self.folder = folder
        self.folder_var.set(folder)

        self.tracking_file = os.path.join(self.folder, "tracking.json")

        # DEFAULTS
        self.tracked_files = {}
        self.file_metadata = {}

        # Load tracking.json if it exists
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, "r") as f:
                    data = json.load(f)

                # Restore tracked_files
                self.tracked_files = {
                    k: float(v) for k, v in data.get("tracked_files", {}).items()
                }

                # Restore file_metadata
                self.file_metadata = data.get("file_metadata", {})
                for fpath, meta in self.file_metadata.items():
                    meta["mod_count"] = int(meta.get("mod_count", 0))
                    meta["history"] = [float(ts) for ts in meta.get("history", [])]

                # FIX: Rebuild tracked_files
                self.tracked_files = {}
                for fpath, meta in self.file_metadata.items():
                    if meta["history"]:
                        self.tracked_files[fpath] = meta["history"][-1]
            except Exception as e:
                print("Failed to load tracking.json:", e)
                # fallback to empty
                self.tracked_files = {}
                self.file_metadata = {}

        # Now scan the folder based on existing metadata
        self._rescan(force=True)


        # Save updated tracking AFTER scan
        self._save_tracking_file()
        
        # Clear charts and hide the export button
        self._clear_charts()

        
    def _auto_rescan(self):
        if self._stop_poll:
            return

        self._rescan()
        self.root.after(REFRESH_INTERVAL_MS, self._auto_rescan)

    def _choose_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.folder or os.path.expanduser('~'))
        if chosen:
            self.load_folder(chosen)


    def _manual_refresh(self):
        self._rescan(force = True)

    
    def _on_close(self):
        self._stop_poll = True
        self.root.destroy()
    
    def _on_year_change(self):
        """Callback when the year range Spinbox is changed."""
        try:
            v = int(self.years_var.get())
        except Exception:
            v = 1
        self.year_range = max(1, min(5, v))  # ensure 1–5
        self._draw_calendar(animate=True)


    # ---------------------------
    # Zoom handling
    # ---------------------------
    def _on_zoom(self, val=None):
        try:
            self.zoom = float(self.zoom_var.get())
        except Exception:
            self.zoom = 1.0
        self.zoom_percent_label.config(text=f"{int(self.zoom*100)}%")
        self._draw_calendar(animate=False)

    # ---------------------------
    # Drawing calendar
    # ---------------------------
    def _draw_calendar(self, animate=True):
        self.canvas.delete('all')
        self.rect_to_date.clear()
        self.date_to_rects.clear()

        today = datetime.date.today()
        days = 365 * self.year_range
        start_date = today - datetime.timedelta(days=days - 1)

        cell = int(self.cell_size * self.zoom)
        box = int(self.box * self.zoom)
        padding_x = 45
        padding_y = 45
        
        # Year label
        year_label = f"{start_date.year} - {today.year}"
        canvas_width = self.canvas.winfo_width() or self.canvas.winfo_reqwidth()
        self.canvas.create_text(canvas_width/2, padding_y - 30, text=year_label, anchor='center', font=(None, int(12 * self.zoom), 'bold'))



        # Weekday labels
        for i, label in enumerate(WEEKDAY_LABELS):
            if label:
                x = padding_x - 10
                y = padding_y + i * cell + box/2
                self.canvas.create_text(x, y, text=label, anchor='e', font=(None, int(9 * self.zoom)))

        # Draw month labels across all years
        col = 0
        current = start_date
        month_positions = {}
        cols = []

        while current <= today:
            if current.weekday() == 0 and current != start_date:
                col += 1
            # include year in key so same month in different years is separate
            month_key = (current.year, current.month)
            if month_key not in month_positions:
                month_positions[month_key] = col
            cols.append(current)
            current += datetime.timedelta(days=1)

        # Draw top month labels
        for (yr, m), cpos in month_positions.items():
            x = padding_x + cpos * cell
            y = padding_y - 12
            self.canvas.create_text(x, y, text=calendar.month_abbr[m], anchor='w', font=(None, int(9 * self.zoom), 'bold'))


        year_label = f"{start_date.year} - {today.year}"
        self.canvas.itemconfig(self.year_label_canvas, text=year_label)

        # Draw day rectangles
        total_cols = math.ceil(len(cols)/7)
        items_to_draw = []
        cur = start_date
        while cur <= today:
            delta = (cur - start_date).days
            col_index = delta // 7
            row = cur.weekday()
            x = padding_x + col_index * cell
            y = padding_y + row * cell
            count = self.contributions.get(cur, 0)
            color = contribution_color(self.palette, count)
            items_to_draw.append((x, y, cur, count, color, box))
            cur += datetime.timedelta(days=1)

        if animate:
            from collections import defaultdict
            by_col = defaultdict(list)
            for x, y, d, c, color, box in items_to_draw:
                colnum = (x - padding_x) // cell
                by_col[colnum].append((x, y, d, c, color, box))
            sorted_cols = sorted(by_col.items(), key=lambda t: t[0])

            def draw_col(idx=0):
                if idx >= len(sorted_cols):
                    return
                colnum, entries = sorted_cols[idx]
                for x, y, d, c, color, box in entries:
                    rid = self.canvas.create_rectangle(x, y, x+box, y+box, fill=color, outline='#889')
                    self.rect_to_date[rid] = d
                    self.date_to_rects[d].append(rid)
                self.root.after(ANIMATION_DELAY_MS, lambda: draw_col(idx+1))
            draw_col(0)
        else:
            for x, y, d, count, color, box in items_to_draw:
                rid = self.canvas.create_rectangle(x, y, x+box, y+box, fill=color, outline='#889')
                self.rect_to_date[rid] = d
                self.date_to_rects[d].append(rid)

        # Legend on canvas
        legend_x = padding_x + total_cols*cell + 20
        ly = padding_y
        for i, lab in enumerate(["0","1","2-3","4-6","7+"]):
            c = contribution_color(self.palette, i if i>0 else 0)
            self.canvas.create_rectangle(legend_x, ly + i*(box+6), legend_x+box, ly + i*(box+6)+box, fill=c, outline='#889')
            self.canvas.create_text(legend_x+box+6, ly + i*(box+6)+box/2, text=lab, anchor='w', font=(None, int(9*self.zoom)))

    # ---------------------------
    # Charts
    # ---------------------------
    def _update_charts(self):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        year = int(self.chart_year_var.get())
        daily_counts = {d: c for d, c in self.contributions.items() if d.year == year}

        if self.chart_canvas_pie:
            self.chart_canvas_pie.get_tk_widget().destroy()
        if self.chart_canvas_line:
            self.chart_canvas_line.get_tk_widget().destroy()
            
        if not self.export_charts_btn.winfo_ismapped():
            self.export_charts_btn.pack(side=tk.LEFT, padx=6)


        # Pie chart
        total = sum(daily_counts.values())
        days = len(daily_counts)
        labels = ['Art Work Done', 'Inactive Days']
        sizes = [total, 365 - days]
        self.fig_pie, ax1 = plt.subplots(figsize=(4,3))
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', textprops={'fontsize':8})
        ax1.set_title(f"Year {year} Overview", fontsize=10)
        self.chart_canvas_pie = FigureCanvasTkAgg(self.fig_pie, master=self.charts_frame)
        self.chart_canvas_pie.draw()
        self.chart_canvas_pie.get_tk_widget().pack(side=tk.LEFT, padx=10,pady=(0, 20))

        # Line graph
        if daily_counts:
            sorted_dates = sorted(daily_counts.keys())
            counts = [daily_counts[d] for d in sorted_dates]
            self.fig_line, ax2 = plt.subplots(figsize=(4,3))
            ax2.plot(sorted_dates, counts)
            ax2.set_title("Daily Contributions", fontsize=10)
            ax2.set_xlabel("Date", fontsize=10)
            ax2.set_ylabel("Art Work Done", fontsize=8)
            ax2.tick_params(axis='x', labelsize=6)  # smaller X-axis labels
            ax2.tick_params(axis='y', labelsize=8)
            self.fig_line.autofmt_xdate()
            self.chart_canvas_line = FigureCanvasTkAgg(self.fig_line, master=self.charts_frame)
            self.chart_canvas_line.draw()
            self.chart_canvas_line.get_tk_widget().pack(side=tk.LEFT, padx=10,pady=(0, 20))
        
        # ---- Bar chart: files by type ----
        from collections import defaultdict

        file_type_counts = defaultdict(int)
        for files in self.files_by_date.values():
            for f in files:
                ext = os.path.splitext(f)[1].lower() or "No Ext"
                file_type_counts[ext] += 1

        # Remove old bar chart if exists
        if hasattr(self, 'chart_canvas_filetypes') and self.chart_canvas_filetypes:
            self.chart_canvas_filetypes.get_tk_widget().destroy()

        if file_type_counts:
            labels = list(file_type_counts.keys())
            counts = [file_type_counts[l] for l in labels]

            x = range(len(labels))

            self.fig_bar, ax3 = plt.subplots(figsize=(4,3))
            ax3.bar(x, counts)

            ax3.set_title(f"Files by Type in {year}", fontsize=10)
            ax3.set_xlabel("File Type", fontsize=10)
            ax3.set_ylabel("Count", fontsize=8)

            ax3.set_xticks(x)
            ax3.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)

            self.fig_bar.tight_layout()

            self.chart_canvas_filetypes = FigureCanvasTkAgg(self.fig_bar, master=self.charts_frame)
            self.chart_canvas_filetypes.draw()
            self.chart_canvas_filetypes.get_tk_widget().pack(side=tk.LEFT, padx=10, pady=(0, 20))



    # ---------------------------
    # Tooltip & click
    # ---------------------------
    def _on_motion(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        items = self.canvas.find_overlapping(x, y, x, y)

        date = None
        for it in items:
            if it in self.rect_to_date:
                date = self.rect_to_date[it]
                break

        if date:
            files = []
            mod_count = 0  # count Work Done/Modifications on THIS day only

            for f, meta in self.file_metadata.items():
                for ts in meta['history']:
                    file_date = datetime.date.fromtimestamp(ts)
                    if file_date == date:
                        mod_count += 1       # one count per modification event
                        files.append(f)      # include file

            # Build tooltip text
            text = f"{human_date(date)}\nWork Done/Modifications: {mod_count}"

            if files:
                # Show file names (unique)
                unique_files = list(dict.fromkeys(files))
                short = '\n'.join(os.path.basename(p) for p in unique_files[:6])
                text += f"\n---\n{short}"

            self._show_tooltip(event.x_root + 12, event.y_root + 12, text)

        else:
            self._hide_tooltip()




    def _on_leave(self, event):
        self._hide_tooltip()

    def _show_tooltip(self, sx, sy, text):
        if self.tooltip is None:
            self.tooltip = tk.Toplevel(self.root)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.attributes('-topmost', True)
            label = tk.Label(self.tooltip, text=text, justify=tk.LEFT, relief=tk.SOLID, borderwidth=1,
                             font=(None, 9), background="#ffffe0")
            label.pack(ipadx=4, ipady=2)
            self.tooltip.label = label
        else:
            self.tooltip.label.config(text=text)
        try:
            self.tooltip.geometry(f"+{sx}+{sy}")
        except Exception:
            pass

    def _hide_tooltip(self):
        if self.tooltip:
            try:
                self.tooltip.destroy()
            except Exception:
                pass
            self.tooltip = None

    def _on_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        items = self.canvas.find_overlapping(x, y, x, y)
        date = None
        for it in items:
            if it in self.rect_to_date:
                date = self.rect_to_date[it]
                break
        if date:
            files = []
            # Gather all files modified/added on this date along with timestamps
            for f in self.file_metadata:
                for hist_mtime in self.file_metadata[f]['history']:
                    file_date = datetime.date.fromtimestamp(hist_mtime)
                    if file_date == date:
                        files.append((f, hist_mtime))
            self._show_files_popup(date, files)






    def _show_files_popup(self, date, files):
        top = tk.Toplevel(self.root)
        top.title(f"Files for {human_date(date)}")
        top.geometry('500x300')
        frm = ttk.Frame(top)
        frm.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        txt = tk.Text(frm)
        txt.pack(fill=tk.BOTH, expand=True)
        if not files:
            txt.insert(tk.END, "No files found for this date.")
        else:
            for f, mtime in files:
                mod_time_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                txt.insert(tk.END, f"{os.path.basename(f)} — {mod_time_str}\n")
        btn = ttk.Button(top, text="Close", command=top.destroy)
        btn.pack(pady=6)


    # ---------------------------
    # Stats
    # ---------------------------
    def _update_stats(self):
        total_days = len(self.contributions)
        total_files = sum(self.contributions.values())
        recent = []
        for d, fls in sorted(self.files_by_date.items(), key=lambda t: t[0], reverse=True):
            for f in fls:
                recent.append((d, f))
                if len(recent) >= 10:
                    break
            if len(recent) >= 10:
                break

        if self.contributions:
            busiest_day = max(self.contributions.items(), key=lambda t: t[1])
            busiest_text = f"{busiest_day[0]}: {busiest_day[1]} files"
        else:
            busiest_text = "N/A"

        s = [
            f"Folder: {self.folder}",
            f"Total files tracked: {total_files}",
            f"Tracked days with files: {total_days}",
            f"Busiest day: {busiest_text}",
            "",
            "Recent files:"
        ]
        for d, f in recent:
            s.append(f"{d} — {os.path.basename(f)}")

        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert(tk.END, '\n'.join(s))
        self.stats_text.config(state=tk.DISABLED)

    # ---------------------------
    # Save to PNG
    # ---------------------------
    def _save_png(self):
        if not PIL_AVAILABLE:
            messagebox.showerror(
                "Pillow missing",
                "Saving as PNG requires Pillow.\nInstall with: pip install pillow"
            )
            return

        # ensure everything is drawn
        self.root.update_idletasks()

        # get canvas position on screen
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        bbox = (x, y, x + w, y + h)

        try:
            img = ImageGrab.grab(bbox)
            f = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png")]
            )
            if f:
                img.save(f, "PNG")
                messagebox.showinfo("Saved", f"Saved calendar to {f}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PNG: {e}")

    
    def _start_tracking(self):
        self.tracking_enabled = True

        if not os.path.exists(self.folder):
            messagebox.showerror("Error", f"Folder does not exist:\n{self.folder}")
            return

        # DO NOT increment counts here
        for entry in os.scandir(self.folder):
            if entry.is_file() and not entry.name.endswith('.json'):
                mtime = entry.stat().st_mtime

                if entry.path not in self.file_metadata:
                    self.file_metadata[entry.path] = {
                        "mtime": mtime,
                        "mod_count": 1,
                        "history": [mtime]
                    }

                self.tracked_files[entry.path] = mtime

        self._save_tracking_file()
        messagebox.showinfo("Tracking Started", "Tracking enabled for folder.")




    
    def _save_tracking_file(self):
        try:
            data = {
                "tracked_files": self.tracked_files,
                "file_metadata": self.file_metadata
            }
            with open(os.path.join(self.folder, "tracking.json"), "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save tracking file: {e}")


    
    def _rescan(self, force = False):
        changed = False
        
        all_files_by_date = get_file_dates(self.folder)

        # ignore JSON files
        self.files_by_date = defaultdict(list)
        for d, files in all_files_by_date.items():
            self.files_by_date[d] = [f for f in files if not f.endswith('.json')]

        # ensure metadata storage exists
        if not hasattr(self, 'file_metadata'):
            self.file_metadata = {}

        for date, files in self.files_by_date.items():
            for f in files:
                try:
                    mtime = os.path.getmtime(f)
                except Exception:
                    continue

                # NEW FILE
                if f not in self.file_metadata:
                    self.file_metadata[f] = {
                        "mtime": mtime,
                        "mod_count": 1,
                        "history": [mtime]
                    }
                    continue

                # Ensure metadata structure is correct (self-healing)
                meta = self.file_metadata[f]
                if "mtime" not in meta or "history" not in meta or "mod_count" not in meta:
                    self.file_metadata[f] = {
                        "mtime": mtime,
                        "mod_count": 1,
                        "history": [mtime]
                    }
                    continue

                # EXISTING FILE → check for modification
                last_mtime = meta["mtime"]

                if mtime > last_mtime + 0.5:
                    meta["mtime"] = mtime
                    meta["mod_count"] += 1
                    
                    # Prevent duplicate history entries
                    if not meta["history"] or mtime > meta["history"][-1]:
                        meta["history"].append(mtime)
                    
                    changed = True

        # update contributions for the calendar
        self.contributions = defaultdict(int)
        for f, data in self.file_metadata.items():
            for ts in data["history"]:
                d = datetime.date.fromtimestamp(ts)
                self.contributions[d] += 1

        
        if changed or force:
            self._update_stats()
            self._draw_calendar(animate=True)
            if changed :
                self._save_tracking_file()
    def _export_charts(self):
        base_path = filedialog.asksaveasfilename(
            title="Export Charts",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")]
        )

        if not base_path:
            return

        base, _ = os.path.splitext(base_path)

        try:
            if hasattr(self, "fig_pie") and self.fig_pie:
                self.fig_pie.savefig(f"{base}_pie.png", dpi=150, bbox_inches="tight")

            if hasattr(self, "fig_line") and self.fig_line:
                self.fig_line.savefig(f"{base}_line.png", dpi=150, bbox_inches="tight")

            if hasattr(self, "fig_bar") and self.fig_bar:
                self.fig_bar.savefig(f"{base}_bar.png", dpi=150, bbox_inches="tight")

            messagebox.showinfo(
                "Exported",
                "Charts exported successfully."
            )

        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
            
    def _clear_charts(self):
        if self.chart_canvas_pie:
            self.chart_canvas_pie.get_tk_widget().destroy()
            self.chart_canvas_pie = None

        if self.chart_canvas_line:
            self.chart_canvas_line.get_tk_widget().destroy()
            self.chart_canvas_line = None

        if hasattr(self, "chart_canvas_filetypes") and self.chart_canvas_filetypes:
            self.chart_canvas_filetypes.get_tk_widget().destroy()
            self.chart_canvas_filetypes = None

        if hasattr(self, "export_charts_btn") and self.export_charts_btn.winfo_ismapped():
            self.export_charts_btn.pack_forget()






        


# ---------------------------
# Run
# ---------------------------
if __name__ == '__main__':
    root = tk.Tk()
    app = ArtworkCalendarApp(root)
    root.geometry('1400x800')
    root.mainloop()
