# SPDX-License-Identifier: MIT
from pathlib import Path

import streamlit as st

# The 3D logo asset is optional and not bundled (it is large). Drop a GLB file at
# ``static/moneyflow.glb`` (relative to where you launch Streamlit) to enable it;
# Streamlit serves it via static file serving. When absent, the logo is skipped.
STATIC_LOGO_PATH = Path("static") / "moneyflow.glb"
STATIC_LOGO_URL = "/app/static/moneyflow.glb"


def render_logo_animation(height: int = 320, compact: bool = False) -> None:
    """Render the optional animated MoneyFlow GLB logo, if the asset is present."""
    if not STATIC_LOGO_PATH.exists():
        return

    min_height = max(120, height)
    radius = "0" if compact else "8px"
    bg = (
        "transparent"
        if compact
        else "linear-gradient(180deg, rgba(23, 107, 95, 0.10), rgba(17, 24, 39, 0.04))"
    )
    exposure = "1.15" if compact else "1.05"
    scale = "0.82 0.82 0.82" if compact else "1 1 1"

    st.iframe(
        f"""
        <script
            type="module"
            src="https://cdn.jsdelivr.net/npm/@google/model-viewer@4.0.0/dist/model-viewer.min.js">
        </script>

        <div id="mf-logo-scene" aria-label="MoneyFlow animated logo">
            <model-viewer
                id="mf-logo-model"
                src=""
                alt="MoneyFlow animated 3D logo"
                auto-rotate
                auto-rotate-delay="0"
                rotation-per-second="28deg"
                camera-orbit="0deg 75deg auto"
                min-camera-orbit="auto auto 80%"
                max-camera-orbit="auto auto 160%"
                interaction-prompt="none"
                disable-zoom
                shadow-intensity="0"
                exposure="{exposure}"
                scale="{scale}"
                loading="eager"
                reveal="auto">
                <div id="mf-logo-fallback" slot="poster">MoneyFlow</div>
            </model-viewer>
            <div id="mf-logo-error">Unable to load 3D logo</div>
        </div>

        <style>
            html, body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
                background: transparent;
            }}

            #mf-logo-scene {{
                width: 100%;
                height: {min_height}px;
                min-height: {min_height}px;
                position: relative;
                overflow: hidden;
                border-radius: {radius};
                background: {bg};
            }}

            #mf-logo-model {{
                display: block;
                width: 100%;
                height: 100%;
                --poster-color: transparent;
                background: transparent;
            }}

            #mf-logo-fallback {{
                height: 100%;
                width: 100%;
                display: grid;
                place-items: center;
                color: #5dd6bc;
                font: 700 1rem system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }}

            #mf-logo-error {{
                display: none;
                position: absolute;
                inset: 0;
                place-items: center;
                color: #5dd6bc;
                font: 700 0.9rem system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }}
        </style>

        <script>
            const model = document.getElementById("mf-logo-model");
            const error = document.getElementById("mf-logo-error");

            // Resolve GLB URL relative to the parent Streamlit server origin
            // so it works on any host, port, or OS (local dev + Cloud)
            try {{
                const origin = window.parent.location.origin;
                model.setAttribute("src", origin + "{STATIC_LOGO_URL}");
            }} catch (e) {{
                // Cross-origin fallback — use absolute path (works on Streamlit Cloud)
                model.setAttribute("src", "{STATIC_LOGO_URL}");
            }}

            model.addEventListener("error", () => {{
                model.style.display = "none";
                error.style.display = "grid";
            }});
        </script>
        """,
        height=height,
    )
