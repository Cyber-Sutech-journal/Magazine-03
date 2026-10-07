import customtkinter as ctk
from tkinter import messagebox
from datetime import date, datetime, timedelta

from models.project import Project
from services.project_manager import ProjectManager
from services.storage import JSONStorage

from ui.dashboard import Dashboard
from ui.project_view import ProjectView


# ============================================================
# COLORS
# ============================================================

BG_COLOR = "#0A0E13"
SIDEBAR_COLOR = "#111720"
CARD_COLOR = "#171E27"
CARD_DARK = "#121921"
INPUT_COLOR = "#10171F"

TEXT_COLOR = "#F4F7FB"
MUTED_COLOR = "#97A3B3"

PRIMARY = "#6C63FF"
PRIMARY_HOVER = "#8078FF"

GREEN = "#22C55E"
GREEN_BG = "#173923"

ORANGE = "#F59E0B"
ORANGE_BG = "#44340F"

RED = "#EF4444"
RED_BG = "#441C20"


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("TickTask")
        self.geometry("1450x900")
        self.minsize(1050, 680)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=BG_COLOR)

        self.storage = JSONStorage()
        self.manager = ProjectManager()
        self.load_projects()

        self.sidebar = None
        self.main_container = None
        self.dashboard = None
        self.project_view = None

        self.build_layout()
        self.show_dashboard()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_projects(self):
        try:
            projects = self.storage.load_projects()
            self.manager.set_projects(projects)
        except Exception as error:
            messagebox.showerror("Load Error", f"Could not load projects.\n\n{error}")

    def save_projects(self):
        try:
            self.storage.save_projects(self.manager.get_all_projects())
            return True
        except Exception as error:
            messagebox.showerror("Save Error", f"Could not save projects.\n\n{error}")
            return False

    def build_layout(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=SIDEBAR_COLOR)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main_container = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        self.main_container.pack(side="left", fill="both", expand=True)

        self.build_sidebar()

    def build_sidebar(self):
        for widget in self.sidebar.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.sidebar, text="TickTask", font=ctk.CTkFont(size=28, weight="bold"), text_color=TEXT_COLOR, justify="left").pack(padx=22, pady=(28, 4), anchor="w")
        ctk.CTkLabel(self.sidebar, text="Project Control Center", font=ctk.CTkFont(size=13), text_color=MUTED_COLOR).pack(padx=22, anchor="w")

        self.create_sidebar_button("⌂   Dashboard", self.show_dashboard)
        self.create_sidebar_button("+   New Project", self.add_project_view)

        ctk.CTkFrame(self.sidebar, height=2, fg_color="#2A3440").pack(fill="x", padx=22, pady=18)

        projects = self.manager.get_all_projects()
        total_projects = len(projects)
        total_tasks = sum(len(p.tasks) for p in projects)
        completed_tasks = sum(len(p.get_completed_tasks()) for p in projects)
        overdue_tasks = 0
        for project in projects:
            for task in project.tasks:
                try:
                    if task.is_overdue(datetime.now()):
                        overdue_tasks += 1
                except TypeError:
                    if task.is_overdue(date.today()):
                        overdue_tasks += 1

        stats_box = ctk.CTkFrame(self.sidebar, fg_color=CARD_COLOR, corner_radius=13)
        stats_box.pack(fill="x", padx=16, pady=3)
        ctk.CTkLabel(stats_box, text="OVERVIEW", font=ctk.CTkFont(size=10, weight="bold"), text_color=MUTED_COLOR).pack(anchor="w", padx=13, pady=(11, 6))
        ctk.CTkLabel(stats_box, text=f"Projects      {total_projects}", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=13, pady=2)
        ctk.CTkLabel(stats_box, text=f"Tasks            {total_tasks}", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=13, pady=2)
        ctk.CTkLabel(stats_box, text=f"Completed   {completed_tasks}", font=ctk.CTkFont(size=12, weight="bold"), text_color=GREEN).pack(anchor="w", padx=13, pady=2)
        ctk.CTkLabel(stats_box, text=f"Overdue      {overdue_tasks}", font=ctk.CTkFont(size=12, weight="bold"), text_color=RED if overdue_tasks > 0 else MUTED_COLOR).pack(anchor="w", padx=13, pady=(2, 12))

        legend = ctk.CTkFrame(self.sidebar, fg_color=CARD_COLOR, corner_radius=13)
        legend.pack(fill="x", padx=16, pady=10)
        ctk.CTkLabel(legend, text="STATUS GUIDE", font=ctk.CTkFont(size=10, weight="bold"), text_color=MUTED_COLOR).pack(anchor="w", padx=13, pady=(11, 5))
        self.create_legend_row(legend, GREEN, "Green", "Safe / On track")
        self.create_legend_row(legend, ORANGE, "Orange", "Warning / Mid-stage")
        self.create_legend_row(legend, RED, "Red", "Danger / Deadline close")

        ctk.CTkLabel(self.sidebar, text="Track the work.\nWatch the time.\nBeat the deadline.", font=ctk.CTkFont(size=12), text_color=MUTED_COLOR, justify="left").pack(side="bottom", padx=22, pady=22, anchor="w")

    def create_sidebar_button(self, text, command):
        ctk.CTkButton(self.sidebar, text=text, command=command, height=47, corner_radius=10, fg_color="transparent", hover_color="#202A36", text_color=TEXT_COLOR, font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(fill="x", padx=18, pady=4)

    def create_legend_row(self, parent, color, title, description):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=3)
        ctk.CTkFrame(row, width=10, height=10, corner_radius=5, fg_color=color).pack(side="left", padx=(0, 7))
        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left")
        ctk.CTkLabel(text_frame, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w")
        ctk.CTkLabel(text_frame, text=description, font=ctk.CTkFont(size=9), text_color=MUTED_COLOR).pack(anchor="w")

    def clear_main(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main()
        self.build_sidebar()
        self.dashboard = Dashboard(
            self.main_container,
            project_manager=self.manager,
            on_open_project=self.open_project_view,
            on_edit_project=self.edit_project_view,
            on_delete_project=self.delete_project_view,
            on_add_project=self.add_project_view
        )
        self.dashboard.pack(fill="both", expand=True)
        self.project_view = None

    def open_project_view(self, project_id):
        project = self.manager.get_project(project_id)
        if project is None:
            messagebox.showerror("Project Not Found", "This project no longer exists.")
            return

        self.clear_main()
        self.project_view = ProjectView(
            self.main_container,
            project=project,
            project_manager=self.manager,
            storage=self.storage,
            on_back=self.show_dashboard,
            on_project_deleted=self.show_dashboard,
            on_project_updated=self.build_sidebar
        )
        self.project_view.pack(fill="both", expand=True)

    def add_project_view(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Create New Project")
        dialog.geometry("590x650")
        dialog.minsize(500, 560)
        dialog.resizable(True, True)
        dialog.configure(fg_color=BG_COLOR)
        dialog.transient(self)
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(dialog, text="Create New Project", font=ctk.CTkFont(size=26, weight="bold"), text_color=TEXT_COLOR).grid(row=0, column=0, sticky="w", padx=25, pady=(20, 5))
        ctk.CTkLabel(dialog, text="Start Date is automatically set to today.", font=ctk.CTkFont(size=11), text_color=MUTED_COLOR).grid(row=0, column=0, sticky="w", padx=25, pady=(52, 0))

        content = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        content.grid_columnconfigure(0, weight=1)

        name_entry = self.create_form_entry(content, "Project Name", "e.g. CyberSutec Magazine", 0)
        description_entry = self.create_form_entry(content, "Description", "What is this project about?", 1)
        start_entry = self.create_form_entry(content, "Start Date", date.today().isoformat(), 2)
        start_entry.configure(state="disabled")

        deadline_box = ctk.CTkFrame(content, fg_color=CARD_COLOR, corner_radius=12)
        deadline_box.grid(row=3, column=0, sticky="ew", padx=7, pady=7)
        ctk.CTkLabel(deadline_box, text="DEADLINE", font=ctk.CTkFont(size=11, weight="bold"), text_color=MUTED_COLOR).pack(anchor="w", padx=14, pady=(11, 2))
        ctk.CTkLabel(deadline_box, text="Enter either the number of days remaining or an exact date.", font=ctk.CTkFont(size=10), text_color=MUTED_COLOR).pack(anchor="w", padx=14, pady=(0, 7))

        deadline_mode = ctk.StringVar(value="days")
        mode_frame = ctk.CTkFrame(deadline_box, fg_color="transparent")
        mode_frame.pack(fill="x", padx=14)
        days_radio = ctk.CTkRadioButton(mode_frame, text="Days remaining", variable=deadline_mode, value="days")
        days_radio.pack(side="left", padx=(0, 18))
        date_radio = ctk.CTkRadioButton(mode_frame, text="Exact date", variable=deadline_mode, value="date")
        date_radio.pack(side="left")

        deadline_entry = ctk.CTkEntry(deadline_box, height=42, fg_color=INPUT_COLOR, font=ctk.CTkFont(size=13))
        deadline_entry.pack(fill="x", padx=14, pady=(8, 3))
        deadline_entry.insert(0, "7")
        deadline_hint = ctk.CTkLabel(deadline_box, text="7 means 7 days from today.", font=ctk.CTkFont(size=10), text_color=MUTED_COLOR)
        deadline_hint.pack(anchor="w", padx=14)

        ctk.CTkLabel(deadline_box, text="Deadline Time", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=14, pady=(8, 4))
        ctk.CTkLabel(deadline_box, text="Use 24-hour format. Example: 23:30", font=ctk.CTkFont(size=10), text_color=MUTED_COLOR).pack(anchor="w", padx=14)

        time_frame = ctk.CTkFrame(deadline_box, fg_color="transparent")
        time_frame.pack(fill="x", padx=14, pady=(5, 5))
        hour_entry = ctk.CTkEntry(time_frame, width=65, height=38, placeholder_text="HH")
        hour_entry.pack(side="left")
        ctk.CTkLabel(time_frame, text=":", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_COLOR).pack(side="left", padx=4)
        minute_entry = ctk.CTkEntry(time_frame, width=65, height=38, placeholder_text="MM")
        minute_entry.pack(side="left")
        hour_entry.insert(0, "23")
        minute_entry.insert(0, "59")

        # Preview label
        preview_label = ctk.CTkLabel(deadline_box, text="Calculated deadline: -", font=ctk.CTkFont(size=11, weight="bold"), text_color=PRIMARY)
        preview_label.pack(anchor="w", padx=14, pady=(2, 11))

        def update_preview():
            try:
                if deadline_mode.get() == "days":
                    days = int(deadline_entry.get().strip())
                    if days < 0:
                        raise ValueError
                    deadline_date = date.today() + timedelta(days=days)
                else:
                    deadline_date = date.fromisoformat(deadline_entry.get().strip())
                hour = int(hour_entry.get().strip())
                minute = int(minute_entry.get().strip())
                if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                    raise ValueError
                deadline = datetime.combine(deadline_date, datetime.min.time()).replace(hour=hour, minute=minute)
                preview_label.configure(text=f"Calculated deadline: {deadline.strftime('%Y-%m-%d  %H:%M')}", text_color=PRIMARY)
            except (ValueError, TypeError):
                preview_label.configure(text="Calculated deadline: Invalid", text_color=RED)

        deadline_entry.bind("<KeyRelease>", lambda event: update_preview())
        hour_entry.bind("<KeyRelease>", lambda event: update_preview())
        minute_entry.bind("<KeyRelease>", lambda event: update_preview())

        def switch_deadline_mode():
            deadline_entry.delete(0, "end")
            if deadline_mode.get() == "days":
                deadline_entry.insert(0, "7")
                deadline_hint.configure(text="7 means 7 days from today.")
            else:
                deadline_entry.insert(0, date.today().isoformat())
                deadline_hint.configure(text="Enter date as YYYY-MM-DD.")
            update_preview()

        days_radio.configure(command=switch_deadline_mode)
        date_radio.configure(command=switch_deadline_mode)
        update_preview()

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.grid(row=2, column=0, sticky="ew", padx=25, pady=15)
        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_columnconfigure(1, weight=1)

        def create_project():
            try:
                name = name_entry.get().strip()
                description = description_entry.get().strip()
                if not name:
                    raise ValueError("Project name is required.")
                start_date = datetime.combine(date.today(), datetime.min.time())
                deadline_text = deadline_entry.get().strip()
                if deadline_mode.get() == "days":
                    days = int(deadline_text)
                    if days < 0:
                        raise ValueError("Days remaining cannot be negative.")
                    deadline_date = date.today() + timedelta(days=days)
                else:
                    deadline_date = date.fromisoformat(deadline_text)
                hour = int(hour_entry.get().strip())
                minute = int(minute_entry.get().strip())
                if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                    raise ValueError("Invalid time.")
                deadline = datetime.combine(deadline_date, datetime.min.time()).replace(hour=hour, minute=minute)
                if start_date >= deadline:
                    raise ValueError("Deadline must be after start.")

                project = Project(
                    name=name,
                    description=description,
                    start_date=start_date,
                    deadline=deadline
                )
                self.manager.add_project(project)
                if self.save_projects():
                    dialog.destroy()
                    self.build_sidebar()
                    self.open_project_view(project.id)
            except (ValueError, TypeError) as error:
                messagebox.showerror("Invalid Project", str(error), parent=dialog)

        ctk.CTkButton(buttons, text="Cancel", command=dialog.destroy, height=45, corner_radius=9, fg_color="#283342", hover_color="#374555").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(buttons, text="Create Project", command=create_project, height=45, corner_radius=9, fg_color=PRIMARY, hover_color=PRIMARY_HOVER).grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def edit_project_view(self, project_id):
        project = self.manager.get_project(project_id)
        if project is None:
            messagebox.showerror("Project Not Found", "Project could not be found.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Project")
        dialog.geometry("600x680")
        dialog.minsize(500, 580)
        dialog.configure(fg_color=BG_COLOR)
        dialog.transient(self)
        dialog.grab_set()
        dialog.grid_rowconfigure(1, weight=1)
        dialog.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(dialog, text="Edit Project", font=ctk.CTkFont(size=27, weight="bold"), text_color=TEXT_COLOR).grid(row=0, column=0, sticky="w", padx=25, pady=(20, 10))

        content = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=15)
        content.grid_columnconfigure(0, weight=1)

        name_entry = self.create_form_entry(content, "Project Name", project.name, 0)
        description_entry = self.create_form_entry(content, "Description", project.description, 1)
        start_entry = self.create_form_entry(content, "Start Date", project.start_date.strftime("%Y-%m-%d"), 2)
        start_entry.configure(state="normal")

        deadline_box = ctk.CTkFrame(content, fg_color=CARD_COLOR, corner_radius=12)
        deadline_box.grid(row=3, column=0, sticky="ew", padx=7, pady=7)
        ctk.CTkLabel(deadline_box, text="Deadline", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=14, pady=(11, 5))

        mode = ctk.StringVar(value="date")
        mode_row = ctk.CTkFrame(deadline_box, fg_color="transparent")
        mode_row.pack(fill="x", padx=14)
        days_radio = ctk.CTkRadioButton(mode_row, text="Days remaining", variable=mode, value="days")
        days_radio.pack(side="left", padx=(0, 18))
        date_radio = ctk.CTkRadioButton(mode_row, text="Exact date", variable=mode, value="date")
        date_radio.pack(side="left")

        deadline_entry = ctk.CTkEntry(deadline_box, height=42, fg_color=INPUT_COLOR)
        deadline_entry.pack(fill="x", padx=14, pady=(8, 6))
        deadline_entry.insert(0, project.deadline.strftime("%Y-%m-%d"))

        ctk.CTkLabel(deadline_box, text="Deadline Time", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=14, pady=(4, 4))
        time_frame = ctk.CTkFrame(deadline_box, fg_color="transparent")
        time_frame.pack(fill="x", padx=14, pady=(0, 12))
        hour_entry = ctk.CTkEntry(time_frame, width=65, height=38, placeholder_text="HH")
        hour_entry.pack(side="left")
        ctk.CTkLabel(time_frame, text=":", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=4)
        minute_entry = ctk.CTkEntry(time_frame, width=65, height=38, placeholder_text="MM")
        minute_entry.pack(side="left")
        hour_entry.insert(0, project.deadline.strftime("%H"))
        minute_entry.insert(0, project.deadline.strftime("%M"))

        def switch_mode():
            deadline_entry.delete(0, "end")
            if mode.get() == "days":
                days = max(0, (project.deadline - datetime.now()).days)
                deadline_entry.insert(0, str(days))
            else:
                deadline_entry.insert(0, project.deadline.strftime("%Y-%m-%d"))

        days_radio.configure(command=switch_mode)
        date_radio.configure(command=switch_mode)

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=25, pady=15)

        def save():
            try:
                name = name_entry.get().strip()
                description = description_entry.get().strip()
                new_start = datetime.combine(date.fromisoformat(start_entry.get().strip()), datetime.min.time())
                deadline_text = deadline_entry.get().strip()
                if mode.get() == "days":
                    days = int(deadline_text)
                    if days < 0:
                        raise ValueError("Days cannot be negative.")
                    deadline_date = date.today() + timedelta(days=days)
                else:
                    deadline_date = date.fromisoformat(deadline_text)
                hour = int(hour_entry.get().strip())
                minute = int(minute_entry.get().strip())
                if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                    raise ValueError("Invalid time.")
                new_deadline = datetime.combine(deadline_date, datetime.min.time()).replace(hour=hour, minute=minute)
                if new_start >= new_deadline:
                    raise ValueError("Start date must be before deadline.")
                if not name:
                    raise ValueError("Project name cannot be empty.")

                project.name = name
                project.description = description
                project.start_date = new_start
                project.deadline = new_deadline

                if self.save_projects():
                    dialog.destroy()
                    self.build_sidebar()
                    self.open_project_view(project.id)
            except (ValueError, TypeError) as error:
                messagebox.showerror("Invalid Project", str(error), parent=dialog)

        ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy, width=120, height=44, fg_color="#283342", hover_color="#374555").pack(side="left")
        ctk.CTkButton(button_frame, text="Save Changes", command=save, width=150, height=44, fg_color=PRIMARY, hover_color=PRIMARY_HOVER).pack(side="right")

    def delete_project_view(self, project_id):
        project = self.manager.get_project(project_id)
        if project is None:
            return
        answer = messagebox.askyesno("Delete Project", f"Delete '{project.name}'?\n\nAll tasks inside this project will also be deleted.")
        if not answer:
            return
        if self.manager.remove_project(project_id):
            if self.save_projects():
                self.build_sidebar()
                self.show_dashboard()

    def create_form_entry(self, parent, label_text, value, row):
        frame = ctk.CTkFrame(parent, fg_color=CARD_COLOR, corner_radius=11)
        frame.grid(row=row, column=0, sticky="ew", padx=7, pady=7)
        ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=13, pady=(10, 4))
        entry = ctk.CTkEntry(frame, height=42, fg_color=INPUT_COLOR, border_color="#303A48")
        entry.pack(fill="x", padx=13, pady=(0, 10))
        if value:
            entry.insert(0, value)
        return entry

    def on_close(self):
        self.save_projects()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()