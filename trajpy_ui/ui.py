import trajpy
from nicegui import ui

from trajpy_ui.backend import compute_selected, handle_multi_upload, plot_trajectories, remove_file, save_results, show_about
from trajpy_ui.config import FEATURES, STATE
from trajpy_ui.utils import find_free_port

ui.markdown(f"# TrajPy GUI — version {trajpy.__version__}")

# ── file list panel (refreshed after every upload / removal) ─────────────────
file_list_container = ui.column().style("gap: 4px")

def refresh_file_list():
    file_list_container.clear()
    with file_list_container:
        if not STATE["uploaded_files"]:
            ui.label("No files uploaded yet.").style("color: grey; font-style: italic")
        else:
            for i, (name, _) in enumerate(STATE["uploaded_files"]):
                with ui.row().style("align-items: center; gap: 8px"):
                    ui.icon("insert_drive_file").style("color: #555")
                    ui.label(name).style("flex-grow: 1")
                    ui.button(
                        icon="close",
                        on_click=lambda _, idx=i: remove_file(idx, STATE, result_box, refresh_file_list),
                    ).props("flat dense round color=negative").tooltip("Remove file")

# ── upload widget ─────────────────────────────────────────────────────────────
with ui.row():
    upload = ui.upload(
        label="Upload one or several files (CSV or YAML)",
        multiple=True,
        auto_upload=True,
        on_multi_upload=lambda event: handle_multi_upload(event, STATE, result_box, refresh_file_list),
    )

refresh_file_list()

# Create a row to place features and plot side by side
with ui.row().style("width: 100%; gap: 20px"):
    # Left column: Features selection
    with ui.column().style("min-width: 300px"):
        with ui.card().tight():
            ui.label("Select features").style("font-weight: bold")
            checkboxes = {}
            for feat in FEATURES:
                cb = ui.checkbox(feat, value=False)
                checkboxes[feat] = cb

    # Right column: Plot container
    plot_container = ui.column().style("flex-grow: 1")

with ui.row():
    about_btn = ui.button("About", on_click=lambda: show_about())

with ui.row():
    compute_btn = ui.button("Compute!", on_click=lambda: compute_selected(STATE, checkboxes, result_box, save_btn))
    plot_btn = ui.button("Plot Trajectories", on_click=lambda: plot_trajectories(STATE, plot_container, result_box))
    save_btn = ui.button("Save results (CSV)", on_click=lambda: save_results(STATE, result_box)).props("disabled")
    result_box = ui.label("No results yet")


if __name__ in {"__main__", "__mp_main__"}:
    port = find_free_port(8080)
    ui.run(port=port)
