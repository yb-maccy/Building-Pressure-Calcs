import tkinter as tk
from tkinter import ttk, messagebox

class DynamicFluidGUI:
    PSI_PER_FOOT = 0.4334

    def __init__(self, root):
        self.root = root
        self.root.title("Hydrostatic Building Pressure Analyzer")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)

        # Application State
        self.floors = []  # List of dicts representing configured floors

        self.setup_styles()
        self.create_layout()
        self.load_defaults()
        self.update_simulation()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        self.style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), foreground="#2c3e50")
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"))
        self.style.configure("Accent.TButton", foreground="white", background="#2980b9")

    def create_layout(self):
        # Main split: Left Control Panel, Right Visualizer
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- LEFT: CONTROL PANEL ---
        self.control_frame = ttk.Frame(self.main_paned, width=350, relief=tk.RAISED)
        self.main_paned.add(self.control_frame, weight=1)

        # Global Config
        global_lbl = ttk.Label(self.control_frame, text="System Configurations", style="Title.TLabel")
        global_lbl.pack(anchor=tk.W, padx=10, pady=10)

        p_frame = ttk.Frame(self.control_frame)
        p_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(p_frame, text="Incoming Supply Pressure (PSI):").pack(side=tk.LEFT)
        self.incoming_p_entry = ttk.Entry(p_frame, width=10)
        self.incoming_p_entry.pack(side=tk.RIGHT, padx=5)
        self.incoming_p_entry.bind("<KeyRelease>", lambda e: self.update_simulation())

        ttk.Separator(self.control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=15)

        # Add Floor Setup
        ttk.Label(self.control_frame, text="Add / Modify Floor Node", style="Header.TLabel").pack(anchor=tk.W, padx=10, pady=5)
        
        f_form = ttk.Frame(self.control_frame)
        f_form.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(f_form, text="Floor Number:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.floor_num_spin = ttk.Spinbox(f_form, from_=-10, to=100, width=8)
        self.floor_num_spin.grid(row=0, column=1, sticky=tk.E, pady=3)

        ttk.Label(f_form, text="Floor Height (ft):").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.floor_h_entry = ttk.Entry(f_form, width=10)
        self.floor_h_entry.grid(row=1, column=1, sticky=tk.E, pady=3)

        ttk.Label(f_form, text="Pump Boost (PSI):").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.pump_entry = ttk.Entry(f_form, width=10)
        self.pump_entry.grid(row=2, column=1, sticky=tk.E, pady=3)

        ttk.Label(f_form, text="PRV Limit (PSI, blank if none):").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.prv_entry = ttk.Entry(f_form, width=10)
        self.prv_entry.grid(row=3, column=1, sticky=tk.E, pady=3)

        btn_add = ttk.Button(self.control_frame, text="Add / Update Floor", command=self.add_or_update_floor)
        btn_add.pack(fill=tk.X, padx=10, pady=10)

        # Active Floors Management List
        ttk.Label(self.control_frame, text="Active Floor Nodes", style="Header.TLabel").pack(anchor=tk.W, padx=10, pady=5)
        self.floor_listbox = tk.Listbox(self.control_frame, height=10, font=("Consolas", 10))
        self.floor_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        btn_delete = ttk.Button(self.control_frame, text="Delete Selected Floor", command=self.delete_floor)
        btn_delete.pack(fill=tk.X, padx=10, pady=5)

        # --- RIGHT: SCHEMATIC VISUALIZER ---
        self.visual_frame = ttk.Frame(self.main_paned, relief=tk.SUNKEN)
        self.main_paned.add(self.visual_frame, weight=3)

        v_title = ttk.Label(self.visual_frame, text="Building Hydrostatic Visualizer Blueprint", style="Title.TLabel")
        v_title.pack(anchor=tk.W, padx=10, pady=10)

        # Legend panel
        legend = ttk.Frame(self.visual_frame)
        legend.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(legend, text="Legend: ", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        tk.Label(legend, text=" <20 PSI Low ", bg="#ffcccc", fg="#cc0000", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=2)
        tk.Label(legend, text=" 20-80 PSI Optimal ", bg="#d4edda", fg="#155724", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=2)
        tk.Label(legend, text=" >80 PSI Critical ", bg="#fff3cd", fg="#856404", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=2)

        # Canvas with a Scrollbar to handle massive buildings cleanly
        canvas_container = ttk.Frame(self.visual_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(canvas_container, bg="#f8f9fa", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind('<Configure>', lambda e: self.draw_building())

    def load_defaults(self):
        """Pre-populates sample building data."""
        self.incoming_p_entry.insert(0, "65.0")
        self.floors = [
            {"num": 3, "height": 10.0, "pump": 25.0, "prv": None},
            {"num": 2, "height": 10.0, "pump": 0.0, "prv": None},
            {"num": 1, "height": 12.0, "pump": 0.0, "prv": None},
            {"num": -1, "height": 12.0, "pump": 0.0, "prv": None},
            {"num": -2, "height": 10.0, "pump": 0.0, "prv": 70.0},
        ]
        self.refresh_floor_listbox()

    def refresh_floor_listbox(self):
        self.floor_listbox.delete(0, tk.END)
        # Sort structural order: Above grade top down, then below grade top down
        self.floors.sort(key=lambda x: x["num"], reverse=True)
        for f in self.floors:
            type_str = "Above Grade" if f["num"] > 0 else "Below Grade"
            pump_str = f" | Pump: +{f['pump']} PSI" if f["pump"] else ""
            prv_str = f" | PRV: {f['prv']} PSI" if f["prv"] else ""
            self.floor_listbox.insert(
                tk.END, f"Flr {f['num']:>3} ({f['height']}ft) [{type_str}]{pump_str}{prv_str}"
            )

    def add_or_update_floor(self):
        try:
            num = int(self.floor_num_spin.get())
            height = float(self.floor_h_entry.get())
            pump = float(self.pump_entry.get() or 0.0)
            prv_val = self.prv_entry.get()
            prv = float(prv_val) if prv_val.strip() else None

            if num == 0:
                messagebox.showerror("Error", "Floor 0 represents street level grade. Use 1 or -1.")
                return

            # Check if updating or creating new
            existing = [f for f in self.floors if f["num"] == num]
            if existing:
                existing[0].update({"height": height, "pump": pump, "prv": prv})
            else:
                self.floors.append({"num": num, "height": height, "pump": pump, "prv": prv})

            self.refresh_floor_listbox()
            self.update_simulation()
        except ValueError:
            messagebox.showerror("Validation Error", "Please ensure Floor Num, Height, and Pumps are numeric values.")

    def delete_floor(self):
        selected_idx = self.floor_listbox.curselection()
        if not selected_idx:
            return
        # Fetch item using listbox text parsing logic or index
        del self.floors[selected_idx[0]]
        self.refresh_floor_listbox()
        self.update_simulation()

    def update_simulation(self):
        """Runs background pipeline math and saves calculated values."""
        try:
            base_pressure = float(self.incoming_p_entry.get() or 0.0)
        except ValueError:
            return # Awaiting proper number inputs

        # Compute Above Grade Floors (ascending order)
        above_floors = sorted([f for f in self.floors if f["num"] > 0], key=lambda x: x["num"])
        current_p = base_pressure
        for f in above_floors:
            current_p -= (f["height"] * self.PSI_PER_FOOT)
            if f["pump"] > 0: current_p += f["pump"]
            if f["prv"] is not None and current_p > f["prv"]: current_p = f["prv"]
            f["calculated_p"] = current_p

        # Compute Below Grade Floors (descending deeper order)
        below_floors = sorted([f for f in self.floors if f["num"] < 0], key=lambda x: x["num"], reverse=True)
        current_p = base_pressure
        for f in below_floors:
            current_p += (f["height"] * self.PSI_PER_FOOT)
            if f["pump"] > 0: current_p += f["pump"]
            if f["prv"] is not None and current_p > f["prv"]: current_p = f["prv"]
            f["calculated_p"] = current_p

        self.draw_building()

    def draw_building(self):
        self.canvas.delete("all")
        
        # UI Scaling Parameters
        canvas_width = self.canvas.winfo_width()
        center_x = canvas_width / 2
        box_width = 320
        box_height = 55
        spacing = 15

        # Filter out into structural presentation stack (Highest floor to lowest basement)
        ordered_floors = sorted(self.floors, key=lambda x: x["num"], reverse=True)
        
        if not ordered_floors:
            self.canvas.create_text(center_x, 100, text="No floors configured yet.", font=("Segoe UI", 12, "italic"))
            return

        # Dynamically set scrolling viewport size
        total_height = len(ordered_floors) * (box_height + spacing) + 120
        self.canvas.configure(scrollregion=(0, 0, canvas_width, total_height))

        # Start drawing from top down
        start_y = 40

        for f in ordered_floors:
            p = f.get("calculated_p", 0.0)

            # Safety Threshold Graphics Color Determination
            if p < 20.0:
                bg_color, border_color, text_color = "#f8d7da", "#dc3545", "#721c24"  # Warning Red
            elif p > 80.0:
                bg_color, border_color, text_color = "#fff3cd", "#ffc107", "#856404"  # Alert Yellow
            else:
                bg_color, border_color, text_color = "#d4edda", "#28a745", "#155724"  # Safe Green

            x1, y1 = center_x - (box_width / 2), start_y
            x2, y2 = center_x + (box_width / 2), start_y + box_height

            # Draw Floor Node Body
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=bg_color, outline=border_color, width=2, tags="floor")
            
            # Floor labels text
            flr_title = f"FLOOR {f['num']}" if f['num'] > 0 else f"BASEMENT {abs(f['num'])}"
            self.canvas.create_text(x1 + 15, y1 + 18, anchor=tk.W, text=flr_title, font=("Segoe UI", 11, "bold"), fill="#2c3e50")
            self.canvas.create_text(x1 + 15, y1 + 38, anchor=tk.W, text=f"Height: {f['height']} ft", font=("Segoe UI", 9, "italic"), fill="#555")

            # Resulting Pressure Output
            self.canvas.create_text(x2 - 15, y1 + 18, anchor=tk.E, text=f"{p:.2f} PSI", font=("Segoe UI", 13, "bold"), fill=text_color)
            
            # Equipment Inline Tags
            equip_text = []
            if f["pump"] > 0: equip_text.append(f"Pump: +{f['pump']} PSI")
            if f["prv"] is not None: equip_text.append(f"PRV: {f['prv']} PSI")
            eq_string = " | ".join(equip_text) if equip_text else "Direct Feed"
            self.canvas.create_text(x2 - 15, y1 + 38, anchor=tk.E, text=eq_string, font=("Segoe UI", 9), fill="#444")

            # Draw connection riser lines between floors
            if f != ordered_floors[-1]:
                self.canvas.create_line(center_x, y2, center_x, y2 + spacing, fill="#7f8c8d", width=3, dash=(4, 2))

            start_y += box_height + spacing

if __name__ == "__main__":
    root = tk.Tk()
    app = DynamicFluidGUI(root)
    root.mainloop()
