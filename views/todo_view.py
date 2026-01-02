import flet as ft
from styles import Colors, PriorityColors
from components.task_item import TaskItem
from utils.suggestions import SUGGESTIONS

class TodoView(ft.Column):
    def __init__(self, data_manager, lang_manager):
        super().__init__()
        self.data_manager = data_manager
        self.lang_manager = lang_manager
        self.scroll = None # Disable main scroll for sticky header support
        self.expand = True
        
        # --- UI Components ---
        
        # shopping list selector
        self.list_dropdown = ft.Dropdown(
            expand=True,
            border_color=Colors.LAVENDER,
            border_radius=30,
            on_change=self.change_list
        )
        
        self.add_list_btn = ft.IconButton(
            icon=ft.Icons.ADD_BOX,
            icon_color=Colors.LAVENDER,
            tooltip=self._t("add_list_tooltip"),
            on_click=self.open_add_list_dialog
        )
        
        self.rename_list_btn = ft.IconButton(
            icon=ft.Icons.EDIT,
            icon_color=Colors.LAVENDER,
            tooltip=self._t("rename_tooltip"),
            on_click=self.open_rename_list_dialog
        )

        self.delete_list_btn = ft.IconButton(
            icon=ft.Icons.DELETE_FOREVER,
            icon_color=ft.Colors.RED_400,
            tooltip=self._t("delete_list_tooltip"),
            on_click=self.confirm_delete_list
        )
        
        self.list_selector_row = ft.Row(
            controls=[
                self.list_dropdown,
                self.rename_list_btn,
                self.delete_list_btn,
                self.add_list_btn
            ],
        )

        # Todo View State
        self.todo_view_mode = "medium"

        # Todo Segmented Control
        self.todo_nav = ft.SegmentedButton(
            selected={"medium"},
            allow_multiple_selection=False,
            on_change=self.toggle_todo_view,
            style=ft.ButtonStyle(
                color={"": ft.Colors.WHITE, "selected": ft.Colors.WHITE},
                bgcolor={"": ft.Colors.TRANSPARENT, "selected": Colors.LAVENDER},
                side={"": ft.BorderSide(1, Colors.LAVENDER)},
            ),
            segments=[
                ft.Segment(
                    value="urgent",
                    label=ft.Text(""), # Compact label, maybe assume icon implies priority or add text back if space permits
                    icon=ft.Icon(ft.Icons.WARNING, color=PriorityColors.URGENT),
                    tooltip=self._t("section_urgent")
                ),
                ft.Segment(
                    value="medium",
                    label=ft.Text(""),
                    icon=ft.Icon(ft.Icons.FIBER_MANUAL_RECORD, color=PriorityColors.MEDIUM),
                    tooltip=self._t("section_medium")
                ),
                ft.Segment(
                    value="low",
                    label=ft.Text(""),
                    icon=ft.Icon(ft.Icons.ARROW_DOWNWARD, color=PriorityColors.LOW),
                    tooltip=self._t("section_low")
                ),
                ft.Segment(
                    value="done",
                    label=ft.Text(""),
                    icon=ft.Icon(ft.Icons.CHECK_CIRCLE, color=PriorityColors.DONE),
                    tooltip=self._t("section_done")
                )
            ]
        )

        # Shopping View State
        self.shopping_view_mode = "open" # "open" or "cart"

        # Shopping Segmented Control
        self.shopping_nav = ft.SegmentedButton(
            selected={"open"},
            allow_multiple_selection=False,
            on_change=self.toggle_shopping_view,
            style=ft.ButtonStyle(
                color={"": ft.Colors.WHITE, "selected": ft.Colors.WHITE},
                bgcolor={"": ft.Colors.TRANSPARENT, "selected": Colors.LAVENDER},
                side={"": ft.BorderSide(1, Colors.LAVENDER)},
            ),
            segments=[
                ft.Segment(
                    value="open",
                    label=ft.Text(self._t("section_open")),
                    icon=ft.Icon(ft.Icons.LIST)
                ),
                ft.Segment(
                    value="cart",
                    label=ft.Text(self._t("section_cart")),
                    icon=ft.Icon(ft.Icons.SHOPPING_CART)
                )
            ]
        )
        
        self.input_field = ft.TextField(
            hint_text=self._t("new_task_hint"),
            expand=True,
            border_radius=30, 
            border_color=Colors.LAVENDER,
            focused_border_color=Colors.LAVENDER,
            cursor_color=Colors.LAVENDER,
            on_change=self.update_suggestions
        )
        
        # Priority Selector (Only visible in Todo Mode)
        self.priority_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("urgent", text=self._t("section_urgent")),
                ft.dropdown.Option("medium", text=self._t("section_medium")),
                ft.dropdown.Option("low", text=self._t("section_low")),
            ],
            value="medium",
            width=150,
            border_radius=30,
            border_color=Colors.LAVENDER,
            focused_border_color=Colors.LAVENDER,
        )

        self.add_btn = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE,
            icon_color=Colors.LAVENDER,
            icon_size=40,
            on_click=self.add_task,
            tooltip=self._t("add_tooltip")
        )

        # Container for inputs
        self.input_row = ft.Row(
            controls=[
                self.input_field,
                self.priority_dropdown, 
                self.add_btn
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # --- Task Columns ---
        self.col_urgent = ft.Column()
        self.col_medium = ft.Column()
        self.col_low = ft.Column()
        self.col_done = ft.Column()
        
        # Shopping specific columns
        self.col_shop_open = ft.Column()
        self.col_shop_cart = ft.Column()
        
        # Suggestions Container (Hidden by default)
        self.suggestions_list = ft.Column(spacing=0)
        self.suggestions_container = ft.Container(
            content=self.suggestions_list,
            visible=False,
            padding=ft.padding.only(left=5, right=5, bottom=5),
            border=ft.border.all(1, Colors.LAVENDER_LIGHT),
            border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10),
        )

        # STRUCTURE FOR STICKY HEADER
        # Header Column: Holds all fixed controls (Inputs, Selectors, Sliders)
        self.header_col = ft.Column(spacing=10)
        
        # Body Column: Holds the scrollable task list
        # expand=True ensures it takes remaining space
        # scroll=ft.ScrollMode.AUTO enables scrolling ONLY within this column
        self.body_col = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

        self.controls = [
            self.header_col,
            self.body_col
        ]
        
        # Initial Load
        self.refresh_view(update_ui=False)

    def did_mount(self):
        """Refreshes the view when added to the page to ensure theme-aware colors are correct."""
        self.refresh_view()

    def _t(self, key):
        return self.lang_manager.get_text(key)
    
    def toggle_shopping_view(self, e):
        # Determine selection
        selected = e.control.selected
        if not selected:
             e.control.selected = {self.shopping_view_mode}
             e.control.update()
             return

        self.shopping_view_mode = list(selected)[0]
        self.refresh_view()
        
    def toggle_todo_view(self, e):
        # Determine selection
        selected = e.control.selected
        if not selected:
             e.control.selected = {self.todo_view_mode}
             e.control.update()
             return

        self.todo_view_mode = list(selected)[0]
        self.refresh_view()

    def close_dialog(self, dialog):
        self.page.close(dialog)
        self.page.update()

    def change_list(self, e):
        new_list_id = self.list_dropdown.value
        mode = self.data_manager.get_settings()["mode"]
        if mode == "shopping":
            self.data_manager.set_current_shopping_list_id(new_list_id)
        else:
             self.data_manager.set_current_todo_list_id(new_list_id)
        self.refresh_view()

    def open_add_list_dialog(self, e):
        self.new_list_name = ft.TextField(hint_text=self._t("new_list_hint"), expand=True, autofocus=True, border_radius=30, border_color=Colors.LAVENDER)
        self.add_list_dialog = ft.AlertDialog(
            title=ft.Text(self._t("add_list_tooltip")),
            content=self.new_list_name,
            actions=[
                ft.TextButton(self._t("cancel"), on_click=lambda e: self.close_dialog(self.add_list_dialog)),
                ft.TextButton(self._t("save"), on_click=self.create_new_list)
            ]
        )
        self.page.open(self.add_list_dialog)

    def create_new_list(self, e):
        name = self.new_list_name.value
        if name:
            mode = self.data_manager.get_settings()["mode"]
            if mode == "shopping":
                self.data_manager.create_shopping_list(name)
            else:
                self.data_manager.create_todo_list(name)
            
            self.new_list_name.value = ""
            self.close_dialog(self.add_list_dialog)
            self.refresh_view()
    
    def open_rename_list_dialog(self, e):
        mode = self.data_manager.get_settings()["mode"]
        if mode == "shopping":
            lists = self.data_manager.get_shopping_lists()
            current_id = self.data_manager.get_current_shopping_list_id()
        else:
            lists = self.data_manager.get_todo_lists()
            current_id = self.data_manager.get_current_todo_list_id()
            
        current_name = lists.get(current_id, "")
        
        self.rename_list_input = ft.TextField(value=current_name, expand=True, autofocus=True, border_radius=30, border_color=Colors.LAVENDER)
        self.rename_list_dialog = ft.AlertDialog(
            title=ft.Text(self._t("rename_list")),
            content=self.rename_list_input,
            actions=[
                ft.TextButton(self._t("cancel"), on_click=lambda e: self.close_dialog(self.rename_list_dialog)),
                ft.TextButton(self._t("save"), on_click=self.rename_list)
            ]
        )
        self.page.open(self.rename_list_dialog)

    def rename_list(self, e):
        new_name = self.rename_list_input.value
        if new_name:
            mode = self.data_manager.get_settings()["mode"]
            if mode == "shopping":
                current_id = self.data_manager.get_current_shopping_list_id()
                self.data_manager.rename_shopping_list(current_id, new_name)
            else:
                current_id = self.data_manager.get_current_todo_list_id()
                self.data_manager.rename_todo_list(current_id, new_name)
                
            self.close_dialog(self.rename_list_dialog)
            self.refresh_view()

    def confirm_delete_list(self, e):
        mode = self.data_manager.get_settings()["mode"]
        if mode == "shopping":
            lists = self.data_manager.get_shopping_lists()
            current_id = self.data_manager.get_current_shopping_list_id()
        else:
            lists = self.data_manager.get_todo_lists()
            current_id = self.data_manager.get_current_todo_list_id()

        current_name = lists.get(current_id, "")
        
        # Check if last list (though implementation should prevent this via disabled button, double check)
        if len(lists) <= 1:
            return

        def delete_action(e):
            if mode == "shopping":
                self.data_manager.delete_shopping_list(current_id)
            else:
                self.data_manager.delete_todo_list(current_id)
            self.close_dialog(self.delete_list_check_dialog)
            self.refresh_view()

        self.delete_list_check_dialog = ft.AlertDialog(
            title=ft.Text(self._t("delete_list_title")),
            content=ft.Text(self._t("delete_list_msg").format(current_name)),
            actions=[
                ft.TextButton(self._t("cancel"), on_click=lambda e: self.close_dialog(self.delete_list_check_dialog)),
                ft.TextButton(self._t("delete_tooltip"), on_click=delete_action, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ]
        )
        self.page.open(self.delete_list_check_dialog)

    def refresh_view(self, update_ui=True):
        # Determine Theme Colors
        # Default to False if page not ready, but did_mount handles that retry
        mode_setting = self.data_manager.get_settings().get("theme_mode", "dark")
        is_light = False
        if self.page:
             is_light = self.page.theme_mode == ft.ThemeMode.LIGHT
        else:
             is_light = (mode_setting == "light")
        
        text_color = ft.Colors.BLACK if is_light else ft.Colors.WHITE
        
        # Update Segmented Button Styles
        # Apply text_color to both states to ensure visibility
        nav_style = ft.ButtonStyle(
            color={"": text_color, "selected": text_color},
            bgcolor={"": ft.Colors.TRANSPARENT, "selected": Colors.LAVENDER},
            side={"": ft.BorderSide(1, Colors.LAVENDER)},
        )
        self.todo_nav.style = nav_style
        self.shopping_nav.style = nav_style
        
        # Update Input Field Colors
        self.input_field.text_style = ft.TextStyle(color=text_color)
        self.input_field.hint_style = ft.TextStyle(color=ft.Colors.GREY_500) # Hint needs to be visible but distinct
        self.input_field.cursor_color = text_color # Cursor matches text
        self.input_field.border_color = Colors.LAVENDER
        
        # Update Dropdown Colors
        # For Dropdown, 'text_style' controls the selected item color
        self.list_dropdown.text_style = ft.TextStyle(color=text_color)
        self.list_dropdown.border_color = Colors.LAVENDER
        
        self.priority_dropdown.text_style = ft.TextStyle(color=text_color)
        self.priority_dropdown.border_color = Colors.LAVENDER

        # Clear main columns
        self.header_col.controls.clear()
        self.body_col.controls.clear()
        
        # Clear sub-columns (task holders)
        self.col_urgent.controls.clear()
        self.col_medium.controls.clear()
        self.col_low.controls.clear()
        self.col_done.controls.clear()
        self.col_shop_open.controls.clear()
        self.col_shop_cart.controls.clear()

        # Reload Settings & Tasks
        settings = self.data_manager.get_settings()
        mode = settings.get("mode", "todo")
        tasks = self.data_manager.get_tasks(mode=mode)
        
        # --- DISTRIBUTE TASKS ---
        # We must distribute tasks FIRST to calculate counts for the UI text
        for t_data in tasks:
            t_item = TaskItem(
                task_name=t_data["name"],
                is_completed=t_data["is_completed"],
                priority=t_data.get("priority", "medium"),
                on_delete=self.delete_task,
                on_status_change=self.toggle_task
            )
            
            if mode == "todo":
                if t_item.is_completed:
                    self.col_done.controls.append(t_item)
                else:
                    if t_item.priority == "urgent":
                        self.col_urgent.controls.append(t_item)
                    elif t_item.priority == "medium":
                        self.col_medium.controls.append(t_item)
                    else:
                        self.col_low.controls.append(t_item)
            else: # Shopping Mode
                if t_item.is_completed:
                    self.col_shop_cart.controls.append(t_item)
                else:
                    self.col_shop_open.controls.append(t_item)

        # --- RECREATE SEGMENTED CONTROLS ---
        # Now we have correct counts and themes
        
        self.todo_nav = ft.SegmentedButton(
            selected={self.todo_view_mode},
            allow_multiple_selection=False,
            on_change=self.toggle_todo_view,
            style=nav_style,
            segments=[
                ft.Segment(
                    value="urgent",
                    label=ft.Text(f"{len(self.col_urgent.controls)}", color=text_color),
                    icon=ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.RED),
                    tooltip=self._t("section_urgent")
                ),
                ft.Segment(
                    value="medium",
                    label=ft.Text(f"{len(self.col_medium.controls)}", color=text_color),
                    icon=ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.AMBER),
                    tooltip=self._t("section_medium")
                ),
                ft.Segment(
                    value="low",
                    label=ft.Text(f"{len(self.col_low.controls)}", color=text_color),
                    icon=ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.GREEN),
                    tooltip=self._t("section_low")
                ),
                ft.Segment(
                    value="done",
                    label=ft.Text(f"{len(self.col_done.controls)}", color=text_color),
                    icon=ft.Icon(ft.Icons.CHECK_CIRCLE, color=PriorityColors.DONE),
                    tooltip=self._t("section_done")
                )
            ]
        )

        self.shopping_nav = ft.SegmentedButton(
            selected={self.shopping_view_mode},
            allow_multiple_selection=False,
            on_change=self.toggle_shopping_view,
            style=nav_style,
            segments=[
                ft.Segment(
                    value="open",
                    label=ft.Text(f"{self._t('section_open')} ({len(self.col_shop_open.controls)})", color=text_color),
                    icon=ft.Icon(ft.Icons.LIST)
                ),
                ft.Segment(
                    value="cart",
                    label=ft.Text(f"{self._t('section_cart')} ({len(self.col_shop_cart.controls)})", color=text_color),
                    icon=ft.Icon(ft.Icons.SHOPPING_CART)
                )
            ]
        )
        
        # --- BUILD HEADER ---
        
        # 1. Spacing at top
        self.header_col.controls.append(ft.Container(height=10))
        
        # 2. List Selector
        self.list_selector_row.visible = True
        self.header_col.controls.append(self.list_selector_row)
        
        # Load Lists for Dropdown
        if mode == "shopping":
            lists = self.data_manager.get_shopping_lists()
            current_list_id = self.data_manager.get_current_shopping_list_id()
        else:
            lists = self.data_manager.get_todo_lists()
            current_list_id = self.data_manager.get_current_todo_list_id()
        
        options = []
        for l_id, l_name in lists.items():
            display_name = l_name
            if l_id == "default":
                display_name = self._t("default_list_name")
            options.append(ft.dropdown.Option(l_id, display_name))
        self.list_dropdown.options = options
        self.list_dropdown.value = current_list_id
        
        # Button States
        if current_list_id == "default":
            self.delete_list_btn.disabled = True
            self.delete_list_btn.icon_color = ft.Colors.GREY_400
            self.rename_list_btn.disabled = True
            self.rename_list_btn.icon_color = ft.Colors.GREY_400
        else:
            self.delete_list_btn.disabled = False
            self.delete_list_btn.icon_color = ft.Colors.RED_400
            self.rename_list_btn.disabled = False
            self.rename_list_btn.icon_color = Colors.LAVENDER

        # 3. Input Area
        hint_key = "new_item_hint" if mode == "shopping" else "new_task_hint"
        self.input_field.hint_text = self._t(hint_key)
        self.priority_dropdown.visible = (mode == "todo")
        self.header_col.controls.append(self.input_row)
        
        # 4. Suggestions
        self.header_col.controls.append(self.suggestions_container)
        
        # 5. Segmented Slider (The core sticky element)
        slider = None
        if mode == "todo":
            slider = self.todo_nav
        else:
            slider = self.shopping_nav
        
        self.header_col.controls.append(
            ft.Container(
                content=slider,
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=10, bottom=5)
            )
        )
        self.header_col.controls.append(ft.Divider(height=10, color="transparent"))

        # --- BUILD BODY TEXT / UPDATES ---
        if mode == "todo":
            # Controls already created above
            
            if self.todo_view_mode == "urgent":
                self.body_col.controls.append(self.col_urgent)
            elif self.todo_view_mode == "medium":
                self.body_col.controls.append(self.col_medium)
            elif self.todo_view_mode == "low":
                self.body_col.controls.append(self.col_low)
            elif self.todo_view_mode == "done":
               self.body_col.controls.append(self.col_done)
        else:
            # Controls already created above
            
            if self.shopping_view_mode == "open":
                self.body_col.controls.append(self.col_shop_open)
            else:
                self.body_col.controls.append(self.col_shop_cart)
        
        
        if update_ui:
            self.update()

    def add_task(self, e):
        if not self.input_field.value:
            return
            
        settings = self.data_manager.get_settings()
        mode = settings.get("mode", "todo")
        
        # shopping mode defaults to medium/no priority concept really, but we store it as medium
        priority = self.priority_dropdown.value if mode == "todo" else "medium"
        
        result = self.data_manager.add_task(
            task_name=self.input_field.value,
            priority=priority,
            is_completed=False,
            mode=mode
        )
        
        if result is None:
             self.page.show_snack_bar(ft.SnackBar(content=ft.Text(self._t("duplicate_warning") if hasattr(self, "_t") else "Item already exists!")))
        else:
             self.input_field.value = ""
             self.suggestions_container.visible = False
             
        self.refresh_view()
        self.refresh_view()

    def delete_task(self, task_item):
        settings = self.data_manager.get_settings()
        mode = settings.get("mode", "todo")
        self.data_manager.delete_task(task_item.task_name, mode=mode)
        self.refresh_view()

    def toggle_task(self, task_item):
        settings = self.data_manager.get_settings()
        mode = settings.get("mode", "todo")
        # Invert status
        new_status = not task_item.is_completed
        self.data_manager.update_task_status(task_item.task_name, new_status, mode=mode)
        self.refresh_view()

    def update_suggestions(self, e):
        query = self.input_field.value.lower()
        self.suggestions_list.controls.clear()
        
        # Only show suggestions in Shopping Mode and if input length > 0
        mode = self.data_manager.get_settings()["mode"]
        if mode == "shopping" and len(query) > 0:
            all_suggestions = self.data_manager.get_all_suggestions()
            matches = [s for s in all_suggestions if s.lower().startswith(query)]
            
            # Limit to top 5 matches
            for match in matches[:5]:
                self.suggestions_list.controls.append(
                    ft.Container(
                        content=ft.Text(match, size=16),
                        padding=10,
                        on_click=lambda e, txt=match: self.use_suggestion(txt),
                        ink=True, # Ripple effect
                        border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.GREY_100))
                    )
                )
            
            has_matches = len(self.suggestions_list.controls) > 0
            self.suggestions_container.visible = has_matches
        else:
            self.suggestions_container.visible = False
            
        self.update()

    def use_suggestion(self, text):
        self.input_field.value = text
        self.suggestions_container.visible = False
        self.update()
        self.input_field.focus()
