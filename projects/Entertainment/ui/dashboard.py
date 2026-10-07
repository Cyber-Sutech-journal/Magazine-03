import customtkinter as ctk
from services.calculator import Calculator


# ============================================================
# COLORS
# ============================================================

BG_COLOR = "#0A0E13"
CARD_COLOR = "#171E27"
CARD_DARK = "#121921"

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


class Dashboard(ctk.CTkFrame):

    def __init__(
        self,
        parent,
        project_manager,
        on_open_project,
        on_edit_project,
        on_delete_project,
        on_add_project
    ):

        super().__init__(parent, fg_color=BG_COLOR)

        self.manager = project_manager

        self.on_open_project = on_open_project
        self.on_edit_project = on_edit_project
        self.on_delete_project = on_delete_project
        self.on_add_project = on_add_project

        self.search_text = ""

        self.build_ui()
        self.refresh()

    def build_ui(self):

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(28, 4))

        ctk.CTkLabel(
            header,
            text="TickTask",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=TEXT_COLOR
        ).pack(side="left")

        ctk.CTkLabel(
            self,
            text="Monitor project progress, time, deadlines and risk.",
            font=ctk.CTkFont(size=13),
            text_color=MUTED_COLOR
        ).pack(anchor="w", padx=30)

        # Search
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=30, pady=(18, 5))
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_frame,
            height=45,
            corner_radius=10,
            fg_color=CARD_DARK,
            border_color="#303A48",
            placeholder_text="Search projects by name or description...",
            font=ctk.CTkFont(size=13)
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 7))
        self.search_entry.bind("<KeyRelease>", self.on_search)

        ctk.CTkButton(
            search_frame,
            text="Clear",
            command=self.clear_search,
            width=78,
            height=45,
            corner_radius=10,
            fg_color="#283342",
            hover_color="#374555"
        ).grid(row=0, column=1)

        self.projects_title = ctk.CTkLabel(
            self,
            text="Your Projects",
            font=ctk.CTkFont(size=23, weight="bold"),
            text_color=TEXT_COLOR
        )
        self.projects_title.pack(anchor="w", padx=30, pady=(16, 8))

        self.projects_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.projects_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 18))

    # Search
    def on_search(self, event=None):
        self.search_text = self.search_entry.get().strip().casefold()
        self.refresh()

    def clear_search(self):
        self.search_entry.delete(0, "end")
        self.search_text = ""
        self.refresh()

    def get_filtered_projects(self):
        projects = self.manager.get_all_projects()
        if not self.search_text:
            return projects
        results = []
        for project in projects:
            name = project.name.casefold()
            description = project.description.casefold()
            if self.search_text in name or self.search_text in description:
                results.append(project)
        return results

    # Colors
    def get_project_colors(self, project):
        status = Calculator.get_project_status(project)
        disaster = Calculator.calculate_disaster_index(project)

        if status == "completed":
            return GREEN, GREEN_BG
        if status == "overdue":
            return RED, RED_BG
        if disaster > 70:
            return RED, RED_BG
        if disaster > 30:
            return ORANGE, ORANGE_BG
        if status == "not_started":
            return ORANGE, ORANGE_BG
        return GREEN, GREEN_BG

    def get_time_color(self, time_progress):
        if time_progress <= 40:
            return GREEN
        if time_progress <= 75:
            return ORANGE
        return RED

    # Helper for remaining time (فقط این بخش تغییر کرده است)
    def format_remaining_time(self, project):
        return Calculator.format_remaining_time(project)

    # Refresh
    def refresh(self):
        for widget in self.projects_scroll.winfo_children():
            widget.destroy()

        projects = self.get_filtered_projects()
        all_projects = self.manager.get_all_projects()

        if not all_projects:
            self.show_empty()
            return
        if not projects:
            self.show_no_results()
            return

        if self.search_text:
            self.projects_title.configure(text=f"Search Results ({len(projects)})")
        else:
            self.projects_title.configure(text="Your Projects")

        projects = sorted(projects, key=lambda project: project.deadline)
        for project in projects:
            self.create_project_card(project)

    def show_empty(self):
        card = ctk.CTkFrame(self.projects_scroll, fg_color=CARD_COLOR, corner_radius=16)
        card.pack(fill="x", padx=12, pady=20)
        ctk.CTkLabel(card, text="No Projects Yet", font=ctk.CTkFont(size=26, weight="bold"), text_color=TEXT_COLOR).pack(pady=(35, 5))
        ctk.CTkLabel(card, text="Use + New Project in the sidebar to create your first project.", font=ctk.CTkFont(size=13), text_color=MUTED_COLOR).pack(pady=(0, 35))

    def show_no_results(self):
        card = ctk.CTkFrame(self.projects_scroll, fg_color=CARD_COLOR, corner_radius=16)
        card.pack(fill="x", padx=12, pady=20)
        ctk.CTkLabel(card, text="No Matching Projects", font=ctk.CTkFont(size=25, weight="bold"), text_color=TEXT_COLOR).pack(pady=(35, 5))
        ctk.CTkLabel(card, text="Try another project name or description.", font=ctk.CTkFont(size=13), text_color=MUTED_COLOR).pack(pady=(0, 35))

    # Project Card
    def create_project_card(self, project):
        try:
            progress = Calculator.calculate_project_progress(project)
            time_progress = Calculator.calculate_time_progress(project)
            remaining_text = self.format_remaining_time(project)
            schedule_gap = Calculator.calculate_schedule_gap(project)
            disaster = Calculator.calculate_disaster_index(project)
            status = Calculator.get_project_status(project)
        except Exception as error:
            self.show_project_error(project, error)
            return

        project_color, project_bg = self.get_project_colors(project)
        time_color = self.get_time_color(time_progress)

        card = ctk.CTkFrame(self.projects_scroll, fg_color=project_bg, corner_radius=16, border_width=2, border_color=project_color)
        card.pack(fill="x", padx=12, pady=6)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(14, 5))

        title_frame = ctk.CTkFrame(top, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(title_frame, text=project.name, font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w")
        desc = project.description.strip() or "No description"
        ctk.CTkLabel(title_frame, text=desc, font=ctk.CTkFont(size=11), text_color=MUTED_COLOR, wraplength=600, justify="left").pack(anchor="w", pady=(2, 0))

        status_names = {
            "not_started": "NOT STARTED",
            "in_progress": "IN PROGRESS",
            "completed": "COMPLETED",
            "overdue": "OVERDUE"
        }
        ctk.CTkLabel(
            top,
            text=status_names.get(status, status.upper()),
            width=145,
            height=34,
            corner_radius=9,
            fg_color=project_bg,
            text_color=project_color,
            font=ctk.CTkFont(size=10, weight="bold")
        ).pack(side="right")

        # Two progress boxes
        progress_container = ctk.CTkFrame(card, fg_color="transparent")
        progress_container.pack(fill="x", padx=18, pady=5)
        progress_container.grid_columnconfigure(0, weight=1)
        progress_container.grid_columnconfigure(1, weight=1)

        project_box = ctk.CTkFrame(progress_container, fg_color=CARD_DARK, corner_radius=12)
        project_box.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        ctk.CTkLabel(project_box, text="PROJECT PROGRESS", font=ctk.CTkFont(size=9, weight="bold"), text_color=MUTED_COLOR).pack(anchor="w", padx=13, pady=(10, 0))
        ctk.CTkLabel(project_box, text=f"{progress:.0f}%", font=ctk.CTkFont(size=28, weight="bold"), text_color=project_color).pack(anchor="w", padx=13)
        bar = ctk.CTkProgressBar(project_box, height=10, corner_radius=5, fg_color="#29333F", progress_color=project_color)
        bar.pack(fill="x", padx=13, pady=(2, 12))
        bar.set(progress / 100)

        time_box = ctk.CTkFrame(progress_container, fg_color=CARD_DARK, corner_radius=12)
        time_box.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        ctk.CTkLabel(time_box, text="TIME PROGRESS", font=ctk.CTkFont(size=9, weight="bold"), text_color=MUTED_COLOR).pack(anchor="w", padx=13, pady=(10, 0))
        ctk.CTkLabel(time_box, text=f"{time_progress:.0f}%", font=ctk.CTkFont(size=28, weight="bold"), text_color=time_color).pack(anchor="w", padx=13)
        tbar = ctk.CTkProgressBar(time_box, height=10, corner_radius=5, fg_color="#29333F", progress_color=time_color)
        tbar.pack(fill="x", padx=13, pady=(2, 3))
        tbar.set(time_progress / 100)
        ctk.CTkLabel(time_box, text=remaining_text, font=ctk.CTkFont(size=10, weight="bold"), text_color=time_color).pack(anchor="w", padx=13, pady=(2, 11))

        # Metrics
        metrics = ctk.CTkFrame(card, fg_color="transparent")
        metrics.pack(fill="x", padx=14, pady=5)
        for i in range(3):
            metrics.grid_columnconfigure(i, weight=1)

        gap_color = RED if schedule_gap > 15 else ORANGE if schedule_gap > 0 else GREEN
        self.create_metric(metrics, 0, "SCHEDULE GAP", f"{schedule_gap:+.1f}%", "Positive = behind schedule.", gap_color)
        self.create_metric(metrics, 1, "DISASTER INDEX", f"{disaster:.0f}/100", "0–30 Safe • 31–70 Warning • 71–100 Danger", project_color)

        if project.tasks:
            total_weight = sum(float(t.weight) for t in project.tasks)
            task_text = f"{len(project.tasks)} tasks  •  W {total_weight:g}"
            task_explanation = "Task count and total weight."
        else:
            task_text = "No tasks"
            task_explanation = "Project progress is entered manually."
        self.create_metric(metrics, 2, "WORK", task_text, task_explanation, TEXT_COLOR)

        # Deadline
        deadline = project.deadline
        ctk.CTkLabel(
            card,
            text=f"Deadline: {deadline.strftime('%Y-%m-%d  %H:%M')}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_COLOR
        ).pack(anchor="w", padx=18, pady=(2, 4))

        # Actions
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=18, pady=(5, 14))

        ctk.CTkButton(actions, text="Open", command=lambda pid=project.id: self.on_open_project(pid), width=105, height=38, corner_radius=9, fg_color=PRIMARY, hover_color=PRIMARY_HOVER, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=3)
        ctk.CTkButton(actions, text="Edit", command=lambda pid=project.id: self.on_edit_project(pid), width=85, height=38, corner_radius=9, fg_color="#283342", hover_color="#374555", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=3)
        ctk.CTkButton(actions, text="Delete", command=lambda pid=project.id: self.on_delete_project(pid), width=85, height=38, corner_radius=9, fg_color=RED_BG, hover_color="#63242A", text_color="#FF9CA3", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=3)

    def create_metric(self, parent, column, title, value, explanation, value_color):
        card = ctk.CTkFrame(parent, fg_color=CARD_DARK, corner_radius=11)
        card.grid(row=0, column=column, sticky="nsew", padx=4)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=8, weight="bold"), text_color=MUTED_COLOR).pack(anchor="w", padx=10, pady=(8, 0))
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=16, weight="bold"), text_color=value_color, wraplength=190, justify="left").pack(anchor="w", padx=10)
        ctk.CTkLabel(card, text=explanation, font=ctk.CTkFont(size=8), text_color=MUTED_COLOR, wraplength=200, justify="left").pack(anchor="w", padx=10, pady=(1, 8))

    def show_project_error(self, project, error):
        card = ctk.CTkFrame(self.projects_scroll, fg_color=RED_BG, corner_radius=12)
        card.pack(fill="x", padx=12, pady=5)
        ctk.CTkLabel(card, text=project.name, font=ctk.CTkFont(size=14, weight="bold"), text_color=RED).pack(anchor="w", padx=13, pady=(10, 2))
        ctk.CTkLabel(card, text=str(error), font=ctk.CTkFont(size=10), text_color=TEXT_COLOR).pack(anchor="w", padx=13, pady=(0, 10))