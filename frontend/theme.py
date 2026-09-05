"""ASCEND design system.

Full mobile-first (iOS PWA) palette, typography, spacing, radii and gradients.
All legacy names (BG, SURFACE, TEXT, ACCENT, ...) are kept as aliases so every
existing screen keeps working unchanged — they simply pick up the new palette.
"""

import flet as ft

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
COLORS = {
    # Backgrounds (elevation expressed through surface colour, not shadows)
    "bg_primary":    "#0F1115",   # page background
    "bg_secondary":  "#1A1D23",   # cards
    "bg_tertiary":   "#242830",   # inputs, hover states
    "bg_elevated":   "#2A2E36",   # bottom sheets, dialogs

    # Text
    "text_primary":    "#FFFFFF",
    "text_secondary":  "#9CA3AF",
    "text_tertiary":   "#6B7280",
    "text_disabled":   "#4B5563",

    # Accents
    "accent_primary":   "#2DD4BF",  # teal
    "accent_secondary": "#A78BFA",  # purple
    "accent_gradient":  ["#2DD4BF", "#A78BFA"],  # for progress indicators

    # Semantic
    "success":  "#10B981",
    "warning":  "#F59E0B",
    "error":    "#EF4444",
    "info":     "#3B82F6",

    # Calendar
    "cal_closed":  "#10B981",
    "cal_partial": "#F59E0B",
    "cal_missed":  "#EF4444",
    "cal_empty":   "#374151",
    "cal_lab":     "#A78BFA",

    # Borders / progress track
    "border":        "#2A2E36",
    "border_active": "#2DD4BF",
    "progress_bg":   "#242830",
}

# Backward-compatible aliases used by the existing screens and components.
BG = COLORS["bg_primary"]
SURFACE = COLORS["bg_secondary"]
TEXT = COLORS["text_primary"]
TEXT_SECONDARY = COLORS["text_secondary"]
TEXT_TERTIARY = COLORS["text_tertiary"]
TEXT_DISABLED = COLORS["text_disabled"]
ACCENT = COLORS["accent_primary"]
PURPLE = COLORS["accent_secondary"]
ERROR = COLORS["error"]
SUCCESS = COLORS["success"]
WARNING = COLORS["warning"]
INFO = COLORS["info"]
MUTED = COLORS["cal_empty"]   # was the body-map "never used" colour
BORDER = COLORS["border"]
RADIUS = 16

# ---------------------------------------------------------------------------
# Gradients
# ---------------------------------------------------------------------------
GRADIENTS = {
    "primary": ft.LinearGradient(
        begin=ft.Alignment.CENTER_LEFT,
        end=ft.Alignment.CENTER_RIGHT,
        colors=list(COLORS["accent_gradient"]),
    ),
    "circular": ft.SweepGradient(
        center=ft.Alignment.CENTER,
        start_angle=0.0,
        end_angle=3.14159 * 2,
        colors=[COLORS["accent_primary"], COLORS["accent_secondary"], COLORS["accent_primary"]],
    ),
}

# ---------------------------------------------------------------------------
# Typography (system font — never set font_family explicitly)
# ---------------------------------------------------------------------------
TYPO = {
    "display_large":  {"size": 32, "weight": ft.FontWeight.BOLD,     "color": TEXT},
    "display":        {"size": 28, "weight": ft.FontWeight.BOLD,     "color": TEXT},
    "headline":       {"size": 22, "weight": ft.FontWeight.BOLD,     "color": TEXT},
    "title":          {"size": 18, "weight": ft.FontWeight.W_600,    "color": TEXT},
    "body":           {"size": 15, "weight": ft.FontWeight.NORMAL,   "color": TEXT},
    "body_secondary": {"size": 15, "weight": ft.FontWeight.NORMAL,   "color": TEXT_SECONDARY},
    "caption":        {"size": 13, "weight": ft.FontWeight.NORMAL,   "color": TEXT_SECONDARY},
    "caption_small":  {"size": 11, "weight": ft.FontWeight.W_500,   "color": TEXT_TERTIARY},
    "button":         {"size": 15, "weight": ft.FontWeight.W_600,    "color": TEXT},
    "tab":            {"size": 11, "weight": ft.FontWeight.W_500,   "color": TEXT_SECONDARY},
    "tab_active":     {"size": 11, "weight": ft.FontWeight.W_600,    "color": ACCENT},
    "metric_value":   {"size": 24, "weight": ft.FontWeight.BOLD,     "color": TEXT},
    "metric_label":   {"size": 11, "weight": ft.FontWeight.NORMAL,   "color": TEXT_SECONDARY},
}


def typo(name: str, **overrides) -> ft.TextStyle:
    """Build a ft.TextStyle from the TYPO table (system font, no font_family)."""
    spec = dict(TYPO[name])
    spec.update(overrides)
    return ft.TextStyle(**spec)


# ---------------------------------------------------------------------------
# Spacing / radii / shadows
# ---------------------------------------------------------------------------
SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 20, "2xl": 24, "3xl": 32, "4xl": 40}

RADII = {
    "sm": 8,     # chips, badges
    "md": 12,    # buttons, inputs
    "lg": 16,    # cards
    "xl": 24,    # bottom sheets (top corners)
    "full": 999,  # pill buttons, avatars
}

# Only for floating elements — on a dark background elevation is done with
# lighter surface colours instead of shadows.
SHADOW_FLOATING = ft.BoxShadow(
    spread_radius=0,
    blur_radius=20,
    color="#00000080",
    offset=ft.Offset(0, 8),
)

# Bottom tab bar: icon+label content height; the home-indicator inset is added
# by ft.SafeArea so the total height becomes ~80 on notched iPhones.
BOTTOM_NAV_CONTENT_HEIGHT = 56

# Touch targets (Apple HIG: 44pt minimum, 48 recommended).
TOUCH_TARGET = 48


def apply_theme(page: ft.Page) -> None:
    """Dark-only iOS-style theme."""
    page.title = "ASCEND"
    page.bgcolor = BG
    page.padding = 0
    page.spacing = 0
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ACCENT,
            secondary=PURPLE,
            error=ERROR,
            surface=SURFACE,
            surface_container_highest=COLORS["bg_elevated"],
        ),
        visual_density=ft.VisualDensity.COMFORTABLE,
        scrollbar_theme=ft.ScrollbarTheme(thumb_color=COLORS["bg_tertiary"]),
    )
    # iOS PWA metadata (harmless no-op where the host doesn't support it).
    if hasattr(page, "meta"):
        page.meta.theme_color = BG
        page.meta.description = "ASCEND — трекер здоровья, тренировок и протокола"
        page.meta.apple_mobile_web_app_capable = True
        page.meta.apple_mobile_web_app_status_bar_style = "black-translucent"
        page.meta.apple_mobile_web_app_title = "ASCEND"
