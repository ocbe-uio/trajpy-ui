
import trajpy
from nicegui import ui

from trajpy_ui.backend import compute_selected, handle_upload, plot_trajectories, save_results, show_about
from trajpy_ui.utils import find_free_port

FEATURES = [
    "Anomalous Exponent",
    "MSD Ratio",
    "Fractal dimension",
    "Anisotropy & Kurtosis",
    "Straightness",
    "Velocity description",
    "Frequency spectrum",
    "Efficiency",
    "Gaussianity",
    "Diffusivity",
    "Confinement Prob.",
]


state = {
    "uploaded_files": [],  # liste av (filename, bytes)
    "trajectories": [],  # liste av tj.Trajectory-objekter
    "selected_features": set(),
    "results": {},
    "last_saved_path": None,
}


ui.markdown(f"# TrajPy GUI — version {trajpy.__version__}")

with ui.row():
    upload = ui.upload(
        label="Upload one or several files (CSV or YAML)",
        multiple=True,
        on_upload=lambda event: handle_upload(event, state, result_box),
    )

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
    compute_btn = ui.button("Compute!", on_click=lambda: compute_selected(state, checkboxes, result_box, save_btn))
    plot_btn = ui.button("Plot Trajectories", on_click=lambda: plot_trajectories(state, plot_container, result_box))
    save_btn = ui.button("Save results (CSV)", on_click=lambda: save_results(state, result_box)).props("disabled")
    result_box = ui.label("No results yet")


if __name__ in {"__main__", "__mp_main__"}:
    port = find_free_port(8080)
    ui.run(port=port)
