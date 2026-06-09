"""Politica frontend permanente para sistemas web modernos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


FRONTEND_POLICY_VERSION = "frontend-quality-1.0"
BEST_PRACTICES_SOURCE = "/Volumes/KINGSTON/CODEX HD/FAbrica FULL UNO /buenas_practicas.md"
BEST_PRACTICES_HASH = "sha256:7261892c7f559de0e9c42510dfc7e6a1c547ede95021510fdc55639d0da84d48"

DESIGN_TOKENS = {
    "color": {
        "primary": "#2563EB",
        "primary_hover": "#1D4ED8",
        "success": "#16A34A",
        "warning": "#F59E0B",
        "error": "#DC2626",
        "info": "#0284C7",
        "background": "#F8FAFC",
        "surface": "#FFFFFF",
        "text": "#0F172A",
        "muted_text": "#64748B",
        "border": "#E2E8F0",
    },
    "typography": {
        "font_family": 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        "sizes_px": {
            "display": 32,
            "page_title": 24,
            "subtitle": 20,
            "body": 16,
            "secondary": 14,
            "label": 14,
            "small": 12,
        },
        "weights": {"regular": 400, "medium": 500, "semibold": 600, "bold": 700},
        "line_height": "1.4-1.6",
    },
    "radius_px": {"control": 8, "card_max": 8},
    "breakpoints": {"sm": 640, "md": 768, "lg": 1024, "xl": 1280, "2xl": 1536},
    "contrast": {"normal_text": 4.5, "large_text": 3.0, "ui_element": 3.0},
}

REQUIRED_COMPONENTS = (
    "Layout",
    "Sidebar",
    "Topbar",
    "Breadcrumbs",
    "Cards",
    "Tables",
    "Forms",
    "Inputs",
    "Selects",
    "DatePicker",
    "Modals",
    "Toasts",
    "Alerts",
    "Tabs",
    "Badges",
    "Pagination",
    "Search",
    "Filters",
    "DropdownMenu",
    "UserMenu",
    "EmptyStates",
    "LoadingSkeletons",
    "ErrorPages",
    "PermissionDeniedPage",
)

SCREEN_STATES = ("loading", "empty", "with_data", "permission_denied", "error", "success")
BUTTON_LEVELS = ("primary", "secondary", "tertiary", "destructive")

PERMANENT_PRACTICES = (
    "Construir simple primero y separar frontend, API, base de datos y workers.",
    "Frontend con Next.js, React, TypeScript, Tailwind CSS y shadcn/ui cuando el proyecto lo autorice.",
    "Validacion fuerte frontend/backend; no confiar en datos enviados por el cliente.",
    "Permisos reales por operacion; no depender solo de frontend.",
    "UI usable sin manual: claridad, consistencia, jerarquia, textos simples, estados claros.",
    "Un boton principal por pantalla; destructivos en rojo y con confirmacion.",
    "Formularios con label visible, validacion inmediata y errores accionables.",
    "Tablas administrativas con busqueda, filtros, ordenamiento, paginacion y acciones por fila.",
    "Toda pantalla cubre loading, empty, with_data, permission_denied, error y success.",
    "Paleta profesional por roles; no depender solo del color.",
    "Contraste WCAG AA: 4.5:1 texto normal, 3:1 texto grande e interfaz.",
    "Tipografia Inter/system-ui, texto normal minimo 16px y line-height 1.4-1.6.",
    "Responsive mobile-first con breakpoints y container queries cuando aplique.",
    "CI/CD con lint, formato, tests, tipos, secretos, vulnerabilidades y aprobacion manual para produccion.",
)


@dataclass(frozen=True)
class ContrastPair:
    foreground: str
    background: str
    minimum: float


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError("hex_color_must_be_6_digits")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def relative_luminance(hex_color: str) -> float:
    rgb = []
    for channel in hex_to_rgb(hex_color):
        normalized = channel / 255
        rgb.append(normalized / 12.92 if normalized <= 0.03928 else ((normalized + 0.055) / 1.055) ** 2.4)
    red, green, blue = rgb
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    lum_a = relative_luminance(foreground)
    lum_b = relative_luminance(background)
    lighter = max(lum_a, lum_b)
    darker = min(lum_a, lum_b)
    return round((lighter + 0.05) / (darker + 0.05), 4)


def validate_design_tokens(tokens: dict[str, Any] | None = None) -> dict[str, Any]:
    tokens = tokens or DESIGN_TOKENS
    required_color_keys = set(DESIGN_TOKENS["color"])
    colors = tokens.get("color", {})
    missing_colors = sorted(required_color_keys - set(colors))
    font_family = tokens.get("typography", {}).get("font_family", "")
    body_size = tokens.get("typography", {}).get("sizes_px", {}).get("body", 0)
    issues = []
    if missing_colors:
        issues.append("missing_color_tokens:" + ",".join(missing_colors))
    if "Inter" not in font_family or "system-ui" not in font_family:
        issues.append("font_family_must_include_inter_and_system_ui")
    if body_size < 16:
        issues.append("body_font_below_16px")
    if tokens.get("radius_px", {}).get("card_max", 0) > 8:
        issues.append("card_radius_above_8px")
    return {
        "status": "pass" if not issues else "fail",
        "issues": issues,
        "policy_version": FRONTEND_POLICY_VERSION,
        "tokens": tokens,
    }


def audit_contrast(tokens: dict[str, Any] | None = None) -> dict[str, Any]:
    tokens = tokens or DESIGN_TOKENS
    colors = tokens["color"]
    pairs = [
        ContrastPair(colors["text"], colors["background"], 4.5),
        ContrastPair(colors["text"], colors["surface"], 4.5),
        ContrastPair(colors["primary"], colors["surface"], 3.0),
        ContrastPair(colors["error"], colors["surface"], 3.0),
        ContrastPair(colors["muted_text"], colors["surface"], 3.0),
    ]
    results = []
    for pair in pairs:
        ratio = contrast_ratio(pair.foreground, pair.background)
        results.append(
            {
                "foreground": pair.foreground,
                "background": pair.background,
                "ratio": ratio,
                "minimum": pair.minimum,
                "status": "pass" if ratio >= pair.minimum else "fail",
            }
        )
    return {
        "status": "pass" if all(item["status"] == "pass" for item in results) else "fail",
        "results": results,
        "policy_version": FRONTEND_POLICY_VERSION,
    }


def responsive_matrix() -> dict[str, Any]:
    return {
        "policy_version": FRONTEND_POLICY_VERSION,
        "strategy": "mobile_first",
        "viewports": [
            {"name": "mobile", "width": 360, "height": 800},
            {"name": "tablet", "width": 768, "height": 1024},
            {"name": "desktop", "width": 1440, "height": 900},
            {"name": "wide", "width": 1920, "height": 1080},
        ],
        "breakpoints": DESIGN_TOKENS["breakpoints"],
        "required_checks": [
            "no_horizontal_overflow",
            "text_no_overlap",
            "primary_action_visible",
            "keyboard_focus_visible",
            "screen_states_present",
            "tables_scroll_or_adapt",
        ],
    }


def frontend_quality_contract() -> dict[str, Any]:
    return {
        "policy_version": FRONTEND_POLICY_VERSION,
        "source": {"path": BEST_PRACTICES_SOURCE, "hash": BEST_PRACTICES_HASH},
        "stack": {
            "frontend": ["Next.js", "React", "TypeScript", "Tailwind CSS", "shadcn/ui"],
            "ui_primitives": ["Radix UI or Base UI via shadcn/ui when authorized"],
            "icons": ["lucide-react when available"],
        },
        "tokens": DESIGN_TOKENS,
        "components": list(REQUIRED_COMPONENTS),
        "screen_states": list(SCREEN_STATES),
        "button_levels": list(BUTTON_LEVELS),
        "permanent_practices": list(PERMANENT_PRACTICES),
        "gates": ["design_system", "ux", "accessibility", "responsive", "visual_qa", "frontend_quality"],
    }
