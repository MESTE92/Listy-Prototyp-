import flet as ft
from styles import Colors

class TaskItem(ft.Dismissible):
    def __init__(self, task_name, on_delete, on_status_change, is_completed=False, priority="medium"):
        self.task_name = task_name
        self.on_delete = on_delete
        self.on_status_change = on_status_change
        self.is_completed = is_completed
        self.priority = priority
        
        # Determine Border Color based on Priority
        from styles import PriorityColors
        if self.is_completed:
            border_color = PriorityColors.DONE
        elif self.priority == "urgent":
            border_color = PriorityColors.URGENT
        elif self.priority == "medium":
            border_color = PriorityColors.MEDIUM
        elif self.priority == "low":
            border_color = PriorityColors.LOW
        else:
            border_color = ft.Colors.GREY_300

        # Inner Visual Container (The actual card look)
        self.inner_container = ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, ft.Colors.GREY_300 if not self.is_completed else ft.Colors.GREY_700),
                left=ft.border.BorderSide(5, border_color)
            ),
            content=ft.Row(
                controls=[
                    ft.Checkbox(
                        label=self.task_name,
                        value=self.is_completed,
                        on_change=lambda e: self.on_status_change(self),
                        active_color=Colors.LAVENDER,
                        check_color=ft.Colors.WHITE,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ft.Colors.RED_400,
                        tooltip="Löschen",
                        on_click=lambda e: self.on_delete(self)
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # Initialize Dismissible
        super().__init__(
            key=task_name, # Key is required for Dismissible
            content=self.inner_container,
            # Left Swipe (Green) -> Mark as Done/Undone
            background=ft.Container(
                bgcolor=ft.Colors.GREEN,
                content=ft.Row([ft.Icon(ft.Icons.CHECK, color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.only(left=20)
            ),
            # Right Swipe (Red) -> Delete
            secondary_background=ft.Container(
                bgcolor=ft.Colors.RED,
                content=ft.Row([ft.Icon(ft.Icons.DELETE, color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.only(right=20)
            ),
            on_dismiss=self.handle_dismiss,
        )

    def handle_dismiss(self, e):
        if e.direction == ft.DismissDirection.END_TO_START: # Swipe Right -> Left (Delete)
            self.on_delete(self)
        elif e.direction == ft.DismissDirection.START_TO_END: # Swipe Left -> Right (Toggle)
            self.on_status_change(self)


