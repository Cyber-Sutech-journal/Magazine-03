import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import date, datetime, timedelta

from models.task import Task
from models.enums import TaskStatus

from services.calculator import Calculator
from services.predictor import Predictor


# ============================================================
# COLORS
# ============================================================

BG_COLOR = "#0A0E13"
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

BORDER = "#2B3542"


class ProjectView(ctk.CTkFrame):

    def __init__(
        self,
        parent,
        project,
        project_manager,
        storage,
        on_back=None,
        on_project_deleted=None,
        on_project_updated=None
    ):
        super().__init__(parent, fg_color=BG_COLOR)

        self.project = project
        self.manager = project_manager
        self.storage = storage

        self.on_back = on_back
        self.on_project_deleted = on_project_deleted
        self.on_project_updated = on_project_updated

        self.selected_task_id = None

        self.build_ui()
        self.refresh()

    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(22, 10))

        ctk.CTkButton(header, text="← Back", command=self.go_back, width=100, height=42, corner_radius=10, fg_color="#283342", hover_color="#374555").pack(side="left")

        self.project_title = ctk.CTkLabel(header, text=self.project.name, font=ctk.CTkFont(size=28, weight="bold"), text_color=TEXT_COLOR)
        self.project_title.pack(side="left", padx=17)

        action_frame = ctk.CTkFrame(header, fg_color="transparent")
        action_frame.pack(side="right")
        ctk.CTkButton(action_frame, text="Edit Project", command=self.edit_project, width=130, height=42, corner_radius=10, fg_color=PRIMARY, hover_color=PRIMARY_HOVER).pack(side="left", padx=3)
        ctk.CTkButton(action_frame, text="Delete", command=self.delete_project, width=100, height=42, corner_radius=10, fg_color=RED_BG, hover_color="#68262E", text_color="#FF9CA3").pack(side="left", padx=3)

        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self.build_summary()
        self.build_prediction()
        self.build_tasks()

    def build_summary(self):
        self.summary_card = ctk.CTkFrame(self.content, fg_color=CARD_COLOR, corner_radius=18)
        self.summary_card.pack(fill="x", padx=8, pady=8)

        self.status_line = ctk.CTkFrame(self.summary_card, height=7, corner_radius=7)
        self.status_line.pack(fill="x", padx=16, pady=(13, 0))

        top = ctk.CTkFrame(self.summary_card, fg_color="transparent")
        top.pack(fill="x", padx=22, pady=(13, 5))

        self.description_label = ctk.CTkLabel(top, text="", font=ctk.CTkFont(size=13), text_color=MUTED_COLOR)
        self.description_label.pack(side="left", fill="x", expand=True, anchor="w")

        self.status_badge = ctk.CTkLabel(
            top,
            text="",
            width=160,
            height=38,
            corner_radius=10,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.status_badge.pack(side="right")

        # Project progress
        project_box = ctk.CTkFrame(
            self.summary_card,
            fg_color=CARD_DARK,
            corner_radius=14
        )
        project_box.pack(
            fill="x",
            padx=22,
            pady=8
        )

        ctk.CTkLabel(
            project_box,
            text="PROJECT PROGRESS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=MUTED_COLOR
        ).pack(
            anchor="w",
            padx=17,
            pady=(13, 0)
        )

        self.project_progress_value = ctk.CTkLabel(
            project_box,
            text="0%",
            font=ctk.CTkFont(size=45, weight="bold")
        )
        self.project_progress_value.pack(
            anchor="w",
            padx=17
        )

        self.project_progress_bar = ctk.CTkProgressBar(
            project_box,
            height=14,
            corner_radius=7,
            fg_color="#29333F"
        )
        self.project_progress_bar.pack(
            fill="x",
            padx=17,
            pady=(2, 13)
        )

        # Time progress
        time_box = ctk.CTkFrame(
            self.summary_card,
            fg_color=CARD_DARK,
            corner_radius=14
        )
        time_box.pack(fill="x", padx=22, pady=8)
        ctk.CTkLabel(time_box, text="TIME PROGRESS", font=ctk.CTkFont(size=12, weight="bold"), text_color=MUTED_COLOR).pack(anchor="w", padx=17, pady=(13, 0))
        self.time_progress_value = ctk.CTkLabel(time_box, text="0%", font=ctk.CTkFont(size=45, weight="bold"))
        self.time_progress_value.pack(anchor="w", padx=17)
        self.time_progress_bar = ctk.CTkProgressBar(time_box, height=14, corner_radius=7, fg_color="#29333F")
        self.time_progress_bar.pack(fill="x", padx=17, pady=(2, 4))
        self.time_message = ctk.CTkLabel(time_box, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.time_message.pack(anchor="w", padx=17, pady=(3, 13))

        # Metrics
        metrics = ctk.CTkFrame(self.summary_card, fg_color="transparent")
        metrics.pack(fill="x", padx=17, pady=8)
        for i in range(4):
            metrics.grid_columnconfigure(i, weight=1)
        self.elapsed_value = self.create_metric(metrics, 0, "ELAPSED", "Time passed since start.")
        self.remaining_value = self.create_metric(metrics, 1, "REMAINING", "Exact time remaining until deadline.")
        self.schedule_value = self.create_metric(metrics, 2, "SCHEDULE GAP", "Time Progress minus Project Progress.")
        self.disaster_value = self.create_metric(metrics, 3, "DISASTER INDEX", "Risk score: 0–30 safe, 31–70 warning, 71–100 danger.")

        # Deadline label
        self.deadline_label = ctk.CTkLabel(self.summary_card, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_COLOR)
        self.deadline_label.pack(anchor="w", padx=22, pady=(3, 17))

    def create_metric(self, parent, column, title, explanation):
        card = ctk.CTkFrame(parent, fg_color=CARD_DARK, corner_radius=12)
        card.grid(row=0, column=column, padx=4, sticky="nsew")
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=9, weight="bold"), text_color=MUTED_COLOR).pack(anchor="w", padx=10, pady=(9, 0))
        value = ctk.CTkLabel(card, text="-", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_COLOR)
        value.pack(anchor="w", padx=10)
        ctk.CTkLabel(card, text=explanation, font=ctk.CTkFont(size=8), text_color=MUTED_COLOR, wraplength=210, justify="left").pack(anchor="w", padx=10, pady=(1, 9))
        return value

    def build_prediction(self):
        card = ctk.CTkFrame(self.content, fg_color=CARD_COLOR, corner_radius=18)
        card.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(card, text="Completion Prediction", font=ctk.CTkFont(size=21, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=21, pady=(16, 2))
        ctk.CTkLabel(card, text="Estimated from the current average project progress rate.", font=ctk.CTkFont(size=12), text_color=MUTED_COLOR).pack(anchor="w", padx=21)
        self.prediction_label = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=25, weight="bold"), text_color=TEXT_COLOR)
        self.prediction_label.pack(anchor="w", padx=21, pady=(13, 0))
        self.prediction_details = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.prediction_details.pack(anchor="w", padx=21, pady=(3, 15))

    def build_tasks(self):
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(13, 5))
        ctk.CTkLabel(header, text="Tasks", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR).pack(side="left")
        self.selection_label = ctk.CTkLabel(header, text="No task selected", font=ctk.CTkFont(size=12, weight="bold"), text_color=MUTED_COLOR)
        self.selection_label.pack(side="left", padx=15)

        buttons = ctk.CTkFrame(header, fg_color="transparent")
        buttons.pack(side="right")
        ctk.CTkButton(buttons, text="+ Add Task", command=self.add_task, width=115, height=40, corner_radius=9, fg_color=PRIMARY, hover_color=PRIMARY_HOVER).pack(side="left", padx=3)
        ctk.CTkButton(buttons, text="Edit Task", command=self.edit_task, width=105, height=40, corner_radius=9, fg_color="#283342", hover_color="#374555").pack(side="left", padx=3)
        ctk.CTkButton(buttons, text="Delete Task", command=self.delete_task, width=110, height=40, corner_radius=9, fg_color=RED_BG, hover_color="#68262E", text_color="#FF9CA3").pack(side="left", padx=3)

        editor = ctk.CTkFrame(self.content, fg_color=CARD_COLOR, corner_radius=14)
        editor.pack(fill="x", padx=8, pady=5)
        ctk.CTkLabel(editor, text="Selected Task Progress", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_COLOR).pack(side="left", padx=(15, 8), pady=13)
        self.progress_input = ctk.CTkEntry(editor, width=85, height=40, fg_color=INPUT_COLOR, border_color=BORDER, placeholder_text="0-100")
        self.progress_input.pack(side="left")
        ctk.CTkLabel(editor, text="%", font=ctk.CTkFont(size=14, weight="bold"), text_color=MUTED_COLOR).pack(side="left", padx=5)
        ctk.CTkButton(editor, text="Apply", command=self.update_selected_progress, width=90, height=40, corner_radius=9, fg_color=PRIMARY, hover_color=PRIMARY_HOVER).pack(side="left", padx=5)
        ctk.CTkLabel(editor, text="Select a task, enter 0–100, then Apply.", font=ctk.CTkFont(size=10), text_color=MUTED_COLOR).pack(side="left", padx=8)

        self.tasks_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.tasks_frame.pack(fill="x", padx=8, pady=4)

    def get_project_colors(self):
        status = Calculator.get_project_status(self.project)
        disaster = Calculator.calculate_disaster_index(self.project)
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

    def refresh(self):
        self.update_summary()
        self.update_prediction()
        self.refresh_tasks()

    def update_summary(self):
        try:
            progress = Calculator.calculate_project_progress(self.project)
            time_progress = Calculator.calculate_time_progress(self.project)
            elapsed_days = Calculator.calculate_time_elapsed(self.project)
            remaining_time = self.format_remaining_time(self.project)
            schedule_gap = Calculator.calculate_schedule_gap(self.project)
            disaster = Calculator.calculate_disaster_index(self.project)
        except Exception as error:
            messagebox.showerror("Calculation Error", str(error))
            return

        project_color, project_bg = self.get_project_colors()
        time_color = self.get_time_color(time_progress)

        self.project_title.configure(text=self.project.name)
        self.description_label.configure(text=self.project.description.strip() or "No project description")
        self.status_line.configure(fg_color=project_color)
        self.status_badge.configure(text=self.get_status_text(), fg_color=project_bg, text_color=project_color)

        self.project_progress_value.configure(text=f"{progress:.0f}%", text_color=project_color)
        self.project_progress_bar.configure(progress_color=project_color)
        self.project_progress_bar.set(progress / 100)
        self.time_progress_value.configure(text=f"{time_progress:.0f}%", text_color=time_color)
        self.time_progress_bar.configure(progress_color=time_color)
        self.time_progress_bar.set(time_progress / 100)
        if progress >= 100:
            msg = "Project completed."
        elif Calculator.is_project_overdue(self.project):
            msg = "The exact deadline has passed."
        elif time_progress <= 40:
            msg = "A lot of time is still available."
        elif time_progress <= 75:
            msg = "The project is in the middle of its timeline."
        else:
            msg = "The deadline is getting close."
        self.time_message.configure(text=msg, text_color=time_color)

        self.elapsed_value.configure(text=f"{elapsed_days:.1f} days")
        self.remaining_value.configure(text=remaining_time)
        if schedule_gap > 0:
            self.schedule_value.configure(text=f"+{schedule_gap:.1f}%", text_color=RED if schedule_gap > 15 else ORANGE)
        else:
            self.schedule_value.configure(text=f"{schedule_gap:.1f}%", text_color=GREEN)
        self.disaster_value.configure(text=f"{disaster:.0f}/100", text_color=project_color)

        deadline = self.project.deadline
        self.deadline_label.configure(text=f"Deadline: {deadline.strftime('%Y-%m-%d  %H:%M')}")

    def get_status_text(self):
        status = Calculator.get_project_status(self.project)
        names = {
            "not_started": "NOT STARTED",
            "in_progress": "IN PROGRESS",
            "completed": "COMPLETED",
            "overdue": "OVERDUE"
        }
        return names.get(status, status.upper())
    def select_task(self, task_id):
        task = self.project.get_task(task_id)
        if task is None:
            messagebox.showerror("Error", "Task was not found.")
            return
        if self.selected_task_id == task_id:
            self.selected_task_id = None
        else:
            self.selected_task_id = task_id
        self.refresh_tasks()

    def get_selected_task(self):
        if self.selected_task_id is None:
            return None
        return self.project.get_task(self.selected_task_id)

    def require_selected_task(self):
        task = self.get_selected_task()
        if task is None:
            messagebox.showwarning("No Task Selected", "Please click SELECT on a task first.")
            return None
        return task

    def update_selected_progress(self):
        task = self.require_selected_task()
        if task is None:
            return
        try:
            value = float(self.progress_input.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Progress", "Enter a number from 0 to 100.")
            return
        if not 0 <= value <= 100:
            messagebox.showerror("Invalid Progress", "Progress must be between 0 and 100.")
            return
        task.update_progress(value)
        if self.save_changes():
            self.refresh()

    def start_task(self, task_id):
        task = self.project.get_task(task_id)
        if task is None:
            return
        task.start()
        if self.save_changes():
            self.refresh()

    def complete_task(self, task_id):
        task = self.project.get_task(task_id)
        if task is None:
            return
        task.complete()
        if self.save_changes():
            self.refresh()

    def reopen_task(self, task_id):
        task = self.project.get_task(task_id)
        if task is None:
            return
        task.reopen()
        if self.save_changes():
            self.refresh()

    def add_task(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Task")
        dialog.geometry("620x720")
        dialog.minsize(520, 620)
        dialog.configure(fg_color=BG_COLOR)
        dialog.grab_set()

        content = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(content, text="Add New Task", font=ctk.CTkFont(size=28, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=15, pady=(10, 18))

        title_entry = self.create_simple_entry(content, "Task Title", "e.g. Design homepage")

        ctk.CTkLabel(content, text="Task Weight", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=15)
        ctk.CTkLabel(content, text="Enter a value > 0 based on importance.", font=ctk.CTkFont(size=10), text_color=MUTED_COLOR).pack(anchor="w", padx=15, pady=(2, 5))
        weight_entry = ctk.CTkEntry(content, height=44, fg_color=INPUT_COLOR)
        weight_entry.pack(fill="x", padx=15, pady=(0, 15))

        deadline_box = ctk.CTkFrame(content, fg_color=CARD_COLOR, corner_radius=12)
        deadline_box.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(deadline_box, text="Task Deadline", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=14, pady=(11, 6))
        deadline_mode = ctk.StringVar(value="days")
        mode_frame = ctk.CTkFrame(deadline_box, fg_color="transparent")
        mode_frame.pack(fill="x", padx=14)
        ctk.CTkRadioButton(mode_frame, text="Days remaining", variable=deadline_mode, value="days").pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(mode_frame, text="Exact date", variable=deadline_mode, value="date").pack(side="left")

        deadline_entry = ctk.CTkEntry(deadline_box, height=44, fg_color=INPUT_COLOR)
        deadline_entry.pack(fill="x", padx=14, pady=8)
        deadline_entry.insert(0, "7")

        ctk.CTkLabel(deadline_box, text="Deadline Time (optional)", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=14, pady=(2, 4))
        time_frame = ctk.CTkFrame(deadline_box, fg_color="transparent")
        time_frame.pack(fill="x", padx=14, pady=(0, 10))
        hour_entry = ctk.CTkEntry(time_frame, width=65, height=38, placeholder_text="HH")
        hour_entry.pack(side="left")
        ctk.CTkLabel(time_frame, text=":", font=ctk.CTkFont(size=17, weight="bold")).pack(side="left", padx=5)
        minute_entry = ctk.CTkEntry(time_frame, width=65, height=38, placeholder_text="MM")
        minute_entry.pack(side="left")

        progress_entry = self.create_simple_entry(content, "Initial Progress", "0-100")
        progress_entry.insert(0, "0")

        def change_deadline_mode():
            deadline_entry.delete(0, "end")
            if deadline_mode.get() == "days":
                deadline_entry.insert(0, "7")
            else:
                deadline_entry.insert(0, date.today().isoformat())

        mode_frame.winfo_children()[0].configure(command=change_deadline_mode)
        mode_frame.winfo_children()[1].configure(command=change_deadline_mode)

        def create():
            try:
                title = title_entry.get().strip()
                if not title:
                    raise ValueError("Task title is required.")
                weight = float(weight_entry.get().strip())
                progress = float(progress_entry.get().strip())
                if weight <= 0:
                    raise ValueError("Task weight must be greater than zero.")
                if not 0 <= progress <= 100:
                    raise ValueError("Progress must be between 0 and 100.")

                deadline_text = deadline_entry.get().strip()
                if deadline_mode.get() == "days":
                    days = int(deadline_text)
                    if days < 0:
                        raise ValueError("Days remaining cannot be negative.")
                    deadline_date = date.today() + timedelta(days=days)
                else:
                    deadline_date = date.fromisoformat(deadline_text)

                hour_text = hour_entry.get().strip()
                minute_text = minute_entry.get().strip()
                if hour_text or minute_text:
                    if not hour_text or not minute_text:
                        raise ValueError("Enter both hour and minute.")
                    hour = int(hour_text)
                    minute = int(minute_text)
                    if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                        raise ValueError("Invalid time.")
                else:
                    hour, minute = 23, 59

                deadline = datetime.combine(deadline_date, datetime.min.time()).replace(hour=hour, minute=minute)

                task = Task(title=title, weight=weight, deadline=deadline)
                task.update_progress(progress)
                self.project.add_task(task)
                if self.save_changes():
                    dialog.destroy()
                    self.selected_task_id = task.id
                    self.refresh()
            except (ValueError, TypeError) as error:
                messagebox.showerror("Invalid Task", str(error), parent=dialog)

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(fill="x", padx=25, pady=15)
        ctk.CTkButton(buttons, text="Cancel", command=dialog.destroy, height=45, fg_color="#283342", hover_color="#374555").pack(side="left")
        ctk.CTkButton(buttons, text="Add Task", command=create, height=45, fg_color=PRIMARY, hover_color=PRIMARY_HOVER).pack(side="right")

    def create_simple_entry(self, parent, label, placeholder=""):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=15, pady=(8, 5))
        entry = ctk.CTkEntry(parent, height=44, fg_color=INPUT_COLOR, border_color=BORDER, placeholder_text=placeholder)
        entry.pack(fill="x", padx=15, pady=(0, 8))
        return entry

    def edit_task(self):
        task = self.require_selected_task()
        if task is None:
            return
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Task")
        dialog.geometry("620x800")
        dialog.configure(fg_color=BG_COLOR)
        dialog.grab_set()

        content = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(content, text="Edit Task", font=ctk.CTkFont(size=28, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=15, pady=(10, 18))

        title_entry = self.create_simple_entry(content, "Task Title")
        title_entry.insert(0, task.title)

        ctk.CTkLabel(content, text="Task Weight", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=15)
        weight_entry = ctk.CTkEntry(content, height=44, fg_color=INPUT_COLOR)
        weight_entry.pack(fill="x", padx=15, pady=(0, 12))
        weight_entry.insert(0, str(task.weight))

        ctk.CTkLabel(content, text="Task Progress", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=15, pady=(6, 2))
        progress_entry = ctk.CTkEntry(content, width=90, height=42, fg_color=INPUT_COLOR)
        progress_entry.pack(anchor="w", padx=15, pady=(0, 5))
        progress_entry.insert(0, str(int(task.progress_percent)))

        deadline_box = ctk.CTkFrame(content, fg_color=CARD_COLOR, corner_radius=12)
        deadline_box.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(deadline_box, text="Task Deadline", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=14, pady=(11, 5))
        mode = ctk.StringVar(value="days")
        mode_row = ctk.CTkFrame(deadline_box, fg_color="transparent")
        mode_row.pack(fill="x", padx=14)
        days_radio = ctk.CTkRadioButton(mode_row, text="Days remaining", variable=mode, value="days")
        days_radio.pack(side="left", padx=(0, 20))
        date_radio = ctk.CTkRadioButton(mode_row, text="Exact date", variable=mode, value="date")
        date_radio.pack(side="left")

        deadline_entry = ctk.CTkEntry(deadline_box, height=44, fg_color=INPUT_COLOR)
        deadline_entry.pack(fill="x", padx=14, pady=8)
        if task.deadline:
            remaining = max(0, (task.deadline - datetime.now()).days)
            deadline_entry.insert(0, str(remaining))

        ctk.CTkLabel(deadline_box, text="Deadline Time", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=14, pady=(2, 5))
        time_row = ctk.CTkFrame(deadline_box, fg_color="transparent")
        time_row.pack(fill="x", padx=14, pady=(0, 12))
        hour_entry = ctk.CTkEntry(time_row, width=65, height=40, placeholder_text="HH")
        hour_entry.pack(side="left")
        ctk.CTkLabel(time_row, text=":", font=ctk.CTkFont(size=17, weight="bold")).pack(side="left", padx=5)
        minute_entry = ctk.CTkEntry(time_row, width=65, height=40, placeholder_text="MM")
        minute_entry.pack(side="left")
        if task.deadline:
            hour_entry.insert(0, task.deadline.strftime("%H"))
            minute_entry.insert(0, task.deadline.strftime("%M"))

        def switch_mode():
            deadline_entry.delete(0, "end")
            if mode.get() == "days":
                if task.deadline:
                    days = max(0, (task.deadline - datetime.now()).days)
                else:
                    days = 7
                deadline_entry.insert(0, str(days))
            else:
                if task.deadline:
                    deadline_entry.insert(0, task.deadline.strftime("%Y-%m-%d"))
                else:
                    deadline_entry.insert(0, date.today().isoformat())

        days_radio.configure(command=switch_mode)
        date_radio.configure(command=switch_mode)

        def save():
            try:
                title = title_entry.get().strip()
                weight = float(weight_entry.get().strip())
                progress = float(progress_entry.get().strip())
                if not title:
                    raise ValueError("Task title cannot be empty.")
                if weight <= 0:
                    raise ValueError("Task weight must be greater than zero.")
                if not 0 <= progress <= 100:
                    raise ValueError("Progress must be between 0 and 100.")

                deadline_text = deadline_entry.get().strip()
                if mode.get() == "days":
                    days = int(deadline_text)
                    if days < 0:
                        raise ValueError("Days cannot be negative.")
                    deadline_date = date.today() + timedelta(days=days)
                else:
                    deadline_date = date.fromisoformat(deadline_text)

                hour_text = hour_entry.get().strip()
                minute_text = minute_entry.get().strip()
                if not hour_text or not minute_text:
                    raise ValueError("Enter both hour and minute.")
                hour = int(hour_text)
                minute = int(minute_text)
                if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                    raise ValueError("Invalid time.")

                deadline = datetime.combine(deadline_date, datetime.min.time()).replace(hour=hour, minute=minute)
                self.project.update_task(task.id, new_title=title, new_weight=weight, new_deadline=deadline, new_progress=progress)
                if self.save_changes():
                    dialog.destroy()
                    self.refresh()
            except (ValueError, TypeError) as error:
                messagebox.showerror("Invalid Task", str(error), parent=dialog)

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(fill="x", padx=25, pady=15)
        ctk.CTkButton(buttons, text="Cancel", command=dialog.destroy, height=45, fg_color="#283342", hover_color="#374555").pack(side="left")
        ctk.CTkButton(buttons, text="Save Changes", command=save, height=45, fg_color=PRIMARY, hover_color=PRIMARY_HOVER).pack(side="right")

    def refresh_tasks(self):
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()
        if not self.project.tasks:
            self.selection_label.configure(text="No task selected")
            self.progress_input.delete(0, "end")
            return
        for task in self.project.tasks:
            self.create_task_card(task)
        selected = self.get_selected_task()
        if selected:
            self.selection_label.configure(text=f"Selected: {selected.title}", text_color=PRIMARY)
            self.progress_input.delete(0, "end")
            self.progress_input.insert(0, str(int(selected.progress_percent)))
        else:
            self.selection_label.configure(text="No task selected", text_color=MUTED_COLOR)

    def create_task_card(self, task):
        selected = task.id == self.selected_task_id
        border_color = PRIMARY if selected else BORDER
        border_width = 2 if selected else 1

        if task.status == TaskStatus.COMPLETED:
            task_color = GREEN
        elif task.status in (TaskStatus.IN_PROGRESS, TaskStatus.REOPENED):
            task_color = ORANGE
        else:
            task_color = MUTED_COLOR

        card = ctk.CTkFrame(self.tasks_frame, fg_color=CARD_COLOR, corner_radius=14, border_width=border_width, border_color=border_color)
        card.pack(fill="x", pady=5)

        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=17, pady=12)
        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text=task.title, font=ctk.CTkFont(size=17, weight="bold"), text_color=TEXT_COLOR).pack(side="left")
        ctk.CTkLabel(title_row, text=task.status.value.replace("_", " ").upper(), font=ctk.CTkFont(size=9, weight="bold"), text_color=task_color).pack(side="left", padx=10)

        deadline_text = task.deadline.strftime("%Y-%m-%d %H:%M") if task.deadline else "No deadline"
        ctk.CTkLabel(left, text=f"Weight: {task.weight:g}   •   Deadline: {deadline_text}", font=ctk.CTkFont(size=11), text_color=MUTED_COLOR).pack(anchor="w", pady=(4, 0))

        progress_bar = ctk.CTkProgressBar(left, height=9, corner_radius=5, fg_color="#29333F", progress_color=task_color)
        progress_bar.pack(fill="x", pady=(8, 3))
        progress_bar.set(task.progress_percent / 100)
        ctk.CTkLabel(left, text=f"{task.progress_percent:.0f}% complete", font=ctk.CTkFont(size=10, weight="bold"), text_color=task_color).pack(anchor="w")

        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=13, pady=12)
        ctk.CTkButton(right, text="✓ SELECTED" if selected else "SELECT", command=lambda tid=task.id: self.select_task(tid), width=125, height=38, corner_radius=9, fg_color=PRIMARY if selected else "#283342", hover_color=PRIMARY_HOVER if selected else "#374555").pack(pady=(0, 6))
        action_row = ctk.CTkFrame(right, fg_color="transparent")
        action_row.pack()
        ctk.CTkButton(action_row, text="Start", command=lambda tid=task.id: self.start_task(tid), width=55, height=32, corner_radius=8, fg_color="#283342", hover_color="#374555").pack(side="left", padx=2)
        ctk.CTkButton(action_row, text="Done", command=lambda tid=task.id: self.complete_task(tid), width=55, height=32, corner_radius=8, fg_color=GREEN_BG, hover_color="#245C38", text_color=GREEN).pack(side="left", padx=2)
        if task.status == TaskStatus.COMPLETED:
            ctk.CTkButton(action_row, text="Reopen", command=lambda tid=task.id: self.reopen_task(tid), width=65, height=32, corner_radius=8, fg_color=ORANGE_BG, hover_color="#5A4212", text_color=ORANGE).pack(side="left", padx=2)

    def delete_task(self):
        task = self.require_selected_task()
        if task is None:
            return
        answer = messagebox.askyesno("Delete Task", f"Delete '{task.title}'?\n\nThis cannot be undone.")
        if not answer:
            return
        self.project.remove_task(task.id)
        self.selected_task_id = None
        if self.save_changes():
            self.refresh()

    def delete_project(self):
        answer = messagebox.askyesno("Delete Project", f"Delete '{self.project.name}'?\n\nAll tasks will also be deleted.")
        if not answer:
            return
        if self.manager.remove_project(self.project.id):
            if self.save_changes():
                if self.on_project_deleted:
                    self.on_project_deleted()
                elif self.on_back:
                    self.on_back()

    def edit_project(self):
        app = self.winfo_toplevel()
        if hasattr(app, "edit_project_view"):
            app.edit_project_view(self.project.id)

    def save_changes(self):
        try:
            self.storage.save_projects(self.manager.get_all_projects())
            if self.on_project_updated:
                self.on_project_updated()
            return True
        except Exception as error:
            messagebox.showerror("Save Error", f"Changes could not be saved.\n\n{error}")
            return False

    def update_prediction(self):
        try:
            predicted = Predictor.predict_completion_date(self.project)
            delay = Predictor.calculate_expected_delay(self.project)
        except Exception:
            predicted = None
            delay = None

        if predicted is None:
            self.prediction_label.configure(text="Not enough progress data")
            self.prediction_details.configure(text="", text_color=MUTED_COLOR)
        else:
            self.prediction_label.configure(text=f"Predicted completion: {predicted.strftime('%Y-%m-%d')}")
            if delay is None:
                self.prediction_details.configure(text="", text_color=MUTED_COLOR)
            elif delay > 0:
                self.prediction_details.configure(text=f"Expected delay: {delay} day(s) late", text_color=RED)
            elif delay < 0:
                self.prediction_details.configure(text=f"Expected: {abs(delay)} day(s) early", text_color=GREEN)
            else:
                self.prediction_details.configure(text="Expected: exactly on deadline", text_color=ORANGE)

    def create_report(self):
        try:
            progress = Calculator.calculate_project_progress(self.project)
            time_progress = Calculator.calculate_time_progress(self.project)
            elapsed = Calculator.calculate_time_elapsed(self.project)
            remaining = self.format_remaining_time(self.project)
            gap = Calculator.calculate_schedule_gap(self.project)
            disaster = Calculator.calculate_disaster_index(self.project)
            status = Calculator.get_project_status(self.project)
        except Exception as error:
            messagebox.showerror("Report Error", str(error))
            return

        deadline = self.project.deadline
        lines = [
            "TICKTASK",
            "PROJECT PROGRESS REPORT",
            "=" * 70,
            "",
            f"Project: {self.project.name}",
            f"Description: {self.project.description}",
            f"Start: {self.project.start_date.strftime('%Y-%m-%d %H:%M')}",
            f"Deadline: {deadline.strftime('%Y-%m-%d %H:%M')}",
            "",
            f"Project Progress: {progress:.2f}%",
            f"Time Progress: {time_progress:.2f}%",
            f"Elapsed Time: {elapsed:.2f} days",
            f"Remaining Time: {remaining}",
            f"Schedule Gap: {gap:.2f}%",
            f"Disaster Index: {disaster:.2f}/100",
            f"Status: {status}",
            ""
        ]

        try:
            predicted = Predictor.predict_completion_date(self.project)
        except Exception:
            predicted = None
        if predicted:
            lines.append(f"Predicted Completion: {predicted.strftime('%Y-%m-%d')}")
        try:
            delay = Predictor.calculate_expected_delay(self.project)
        except Exception:
            delay = None
        if delay is not None:
            lines.append(f"Expected Delay: {delay} day(s)")
        lines.append("")
        lines.append("TASKS")
        lines.append("-" * 70)
        for idx, task in enumerate(self.project.tasks, start=1):
            task_deadline = task.deadline.strftime("%Y-%m-%d %H:%M") if task.deadline else "None"
            lines.append(f"{idx}. {task.title}")
            lines.append(f"   Weight: {task.weight}")
            lines.append(f"   Progress: {task.progress_percent:.2f}%")
            lines.append(f"   Status: {task.status.value}")
            lines.append(f"   Deadline: {task_deadline}")
            lines.append("")

        report_text = "\n".join(lines)
        dialog = ctk.CTkToplevel(self)
        dialog.title("Progress Report")
        dialog.geometry("850x700")
        dialog.minsize(650, 500)
        dialog.configure(fg_color=BG_COLOR)
        ctk.CTkLabel(dialog, text="Project Progress Report", font=ctk.CTkFont(size=27, weight="bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=22, pady=(20, 8))
        text_box = ctk.CTkTextbox(dialog, fg_color=CARD_COLOR, text_color=TEXT_COLOR, font=ctk.CTkFont(family="Consolas", size=12), corner_radius=12)
        text_box.pack(fill="both", expand=True, padx=22, pady=8)
        text_box.insert("1.0", report_text)
        text_box.configure(state="disabled")
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=22, pady=12)
        ctk.CTkButton(button_frame, text="Close", command=dialog.destroy, width=120, height=43, fg_color="#283342", hover_color="#374555").pack(side="left")
        ctk.CTkButton(button_frame, text="Save Report", command=lambda: self._save_report(report_text), width=150, height=43, fg_color=PRIMARY, hover_color=PRIMARY_HOVER).pack(side="right")

    def _save_report(self, report_text):
        path = filedialog.asksaveasfilename(title="Save Progress Report", defaultextension=".txt", filetypes=[("Text File", "*.txt")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(report_text)
            messagebox.showinfo("Saved", "Report saved successfully.")
        except Exception as error:
            messagebox.showerror("Save Error", str(error))

    def go_back(self):
        if self.on_back:
            self.on_back()