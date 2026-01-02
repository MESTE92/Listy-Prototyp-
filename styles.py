import flet as ft

# Colors
class Colors:
    LAVENDER = "#9575CD"  # Primary Lavender for Buttons/Highlights
    LAVENDER_LIGHT = "#D1C4E9" # Lighter shade
    LAVENDER_BG_LIGHT = "#F3E5F5" # Very light tint for backgrounds if needed
    
    TEXT_LIGHT = "#000000"
    TEXT_DARK = "#FFFFFF"
    
    BG_LIGHT = "#FFFFFF"
    BG_DARK = "#121212"

def get_theme(mode: ft.ThemeMode):
    # We can customize the theme data here if needed
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=Colors.LAVENDER,
            secondary=Colors.LAVENDER_LIGHT,
        )
    )

class PriorityColors:
    URGENT = ft.Colors.RED_600   # "Rot"
    MEDIUM = ft.Colors.ORANGE_800 # "Dunkles Orange"
    LOW = ft.Colors.GREEN        # "Grün"
    DONE = ft.Colors.GREY_400
