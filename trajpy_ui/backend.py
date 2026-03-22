import base64
import os
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from nicegui import ui
from PIL import Image
from trajpy import trajpy as tj


def load_trajectories_from_uploads(uploads):
    trs = []
    for idx, (name, content) in enumerate(uploads):
        lower = name.lower()
        if lower.endswith(".yaml") or lower.endswith(".yml"):
            from trajpy.auxiliar_functions import parse_lammps_dump_yaml

            try:
                positions = parse_lammps_dump_yaml(BytesIO(content))
            except Exception:
                # Use unique temporary filename with index
                tmp = f"/tmp/{idx}_{name}"
                with open(tmp, "wb") as f:
                    f.write(content)
                positions = parse_lammps_dump_yaml(tmp)
                os.remove(tmp)
            num_atoms = positions.shape[1]
            for atom_idx in range(num_atoms):
                atom_trajectory = positions[:, atom_idx, :]
                trs.append(tj.Trajectory(atom_trajectory))
        else:
            # Use unique temporary filename with index
            tmp = f"/tmp/{idx}_{name}"
            with open(tmp, "wb") as f:
                f.write(content)
            try:
                trs.append(tj.Trajectory(tmp, skip_header=1, delimiter=","))
            except Exception as e:
                print(f"Error loading {name}: {e}")
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
    return trs


def normalize_upload_event(event):
    """
    Normalize NiceGUI upload event into a list of (name, bytes).
    Works for different NiceGUI versions / shapes and for single or multiple files.
    """
    if event is None:
        return []

    normalized = []

    # NiceGUI passes event with a 'file' attribute (single file)
    if hasattr(event, "file"):
        f = event.file
        name = f.name
        # Read the content from the _data attribute
        content = f._data if hasattr(f, "_data") else f.read()
        if hasattr(content, "read"):
            content = content.read()
        normalized.append((name, content))

    # Handle multiple files if event has 'files' attribute
    elif hasattr(event, "files"):
        for f in event.files:
            name = f.name
            content = f._data if hasattr(f, "_data") else f.read()
            if hasattr(content, "read"):
                content = content.read()
            normalized.append((name, content))
    else:
        raise RuntimeError(f"Could not parse upload event: {repr(event)}")

    return normalized


def remove_file(index, state, result_box, refresh_fn):
    """Remove an uploaded file by index, reload trajectories and refresh the file list."""
    try:
        state["uploaded_files"].pop(index)
        state["trajectories"] = load_trajectories_from_uploads(state["uploaded_files"])
        n = len(state["uploaded_files"])
        result_box.set_text(
            f"{len(state['trajectories'])} trajectory(ies) loaded from {n} file(s)" if n > 0 else "No files uploaded"
        )
    except Exception as e:
        result_box.set_text(f"Error removing file: {e}")
    finally:
        refresh_fn()


def handle_upload(event, state, result_box, refresh_fn=None):
    """Handle a single-file upload event (on_upload, fires once per file)."""
    try:
        uploaded = normalize_upload_event(event)
        state["uploaded_files"].extend(uploaded)
        state["trajectories"] = load_trajectories_from_uploads(state["uploaded_files"])
        result_box.set_text(
            f"{len(state['trajectories'])} trajectory(ies) loaded from {len(state['uploaded_files'])} file(s)"
        )
    except Exception as e:
        result_box.set_text(f"Error loading files: {e}")
    finally:
        if refresh_fn:
            refresh_fn()


def handle_multi_upload(event, state, result_box, refresh_fn=None):
    """Handle a multi-file upload event (on_multi_upload, fires once with all files).
    event.files is a list of FileUpload objects.
    """
    try:
        for f in event.files:
            name = f.name
            content = f._data if hasattr(f, "_data") else f.read()
            if hasattr(content, "read"):
                content = content.read()
            state["uploaded_files"].append((name, content))

        state["trajectories"] = load_trajectories_from_uploads(state["uploaded_files"])
        result_box.set_text(
            f"{len(state['trajectories'])} trajectory(ies) loaded from {len(state['uploaded_files'])} file(s)"
        )
    except Exception as e:
        result_box.set_text(f"Error loading files: {e}")
    finally:
        if refresh_fn:
            refresh_fn()


def compute_selected(state: dict, checkboxes: dict, result_box, save_btn):
    if not state["trajectories"]:
        result_box.set_text("Ingen trajectories lastet inn")
        return

    selected = [feat for feat, cb in checkboxes.items() if cb.value]
    state["results"] = {}
    errors = []

    for n, trajectory in enumerate(state["trajectories"]):
        r = trajectory
        state["results"][n] = {}

        if any("Anomalous" in feature for feature in selected):
            try:
                r.msd_ea = r.msd_ensemble_averaged_(r._r)
                r.anomalous_exponent = r.anomalous_exponent_(r.msd_ea, r._t)
                if np.isnan(r.anomalous_exponent) or np.isinf(r.anomalous_exponent):
                    state["results"][n]["alpha"] = "NaN"
                else:
                    state["results"][n]["alpha"] = r.anomalous_exponent
            except Exception as e:
                errors.append(f"Trajectory {n + 1}: Anomalous Exponent - {str(e)}")
                state["results"][n]["alpha"] = "Error"

        if any("MSD" in feature for feature in selected):
            try:
                r.msd_ta = r.msd_time_averaged_(r._r, np.arange(len(r._r)))
                r.msd_ratio = r.msd_ratio_(r.msd_ta, n1=2, n2=10)
                if np.isnan(r.msd_ratio) or np.isinf(r.msd_ratio):
                    state["results"][n]["msd_ratio"] = "NaN"
                else:
                    state["results"][n]["msd_ratio"] = r.msd_ratio
            except Exception as e:
                errors.append(f"Trajectory {n + 1}: MSD Ratio - {str(e)}")
                state["results"][n]["msd_ratio"] = "Error"

        if any("Fractal" in feature for feature in selected):
            try:
                r.fractal_dimension, r._r0 = r.fractal_dimension_(r._r)
                if np.isnan(r.fractal_dimension) or np.isinf(r.fractal_dimension):
                    state["results"][n]["df"] = "NaN"
                else:
                    state["results"][n]["df"] = r.fractal_dimension
            except Exception as e:
                errors.append(f"Trajectory {n + 1}: Fractal Dimension - {str(e)}")
                state["results"][n]["df"] = "Error"

        if any(item in feature for feature in selected for item in ["Kurtosis", "Anisotropy"]):
            try:
                gyration_radius_dict = r.gyration_radius_(r._r)
                r.gyration_radius = gyration_radius_dict["gyration tensor"]
                r.eigenvalues = gyration_radius_dict["eigenvalues"]
                r.eigenvectors = gyration_radius_dict["eigenvectors"]
                r.kurtosis = r.kurtosis_(r._r, r.eigenvectors[:, 0])
                r.anisotropy = r.anisotropy_(r.eigenvalues)

                if np.isnan(r.anisotropy) or np.isinf(r.anisotropy):
                    state["results"][n]["anisotropy"] = "NaN"
                else:
                    state["results"][n]["anisotropy"] = r.anisotropy

                if np.isnan(r.kurtosis) or np.isinf(r.kurtosis):
                    state["results"][n]["kurtosis"] = "NaN"
                else:
                    state["results"][n]["kurtosis"] = r.kurtosis
            except Exception as e:
                errors.append(f"Trajectory {n + 1}: Anisotropy/Kurtosis - {str(e)}")
                state["results"][n]["anisotropy"] = "Error"
                state["results"][n]["kurtosis"] = "Error"

        if any("Gaussianity" in feature for feature in selected):
            try:
                r.gaussianity = r.gaussianity_(r._r)
                if np.isnan(r.gaussianity) or np.isinf(r.gaussianity):
                    state["results"][n]["gaussianity"] = "NaN"
                else:
                    state["results"][n]["gaussianity"] = r.gaussianity
            except Exception as e:
                errors.append(f"Trajectory {n + 1}: Gaussianity - {str(e)}")
                state["results"][n]["gaussianity"] = "Error"

        if any("Straightness" in feature for feature in selected):
            try:
                r.straightness = r.straightness_(r._r)
                if np.isnan(r.straightness) or np.isinf(r.straightness):
                    state["results"][n]["straightness"] = "NaN"
                else:
                    state["results"][n]["straightness"] = r.straightness
            except Exception as e:
                errors.append(f"Trajectory {n + 1}: Straightness - {str(e)}")
                state["results"][n]["straightness"] = "Error"

        if any("Velocity description" in feature for feature in selected):
            try:
                if not isinstance(r.velocity, np.ndarray):
                    r.velocity = r.velocity_(r._r, r._t)
                r.velocity_description = r.velocity_description_(r.velocity)

                axis_labels = ["x", "y", "z"]
                n_dims = r.velocity.shape[1] if r.velocity.ndim > 1 else 1

                # Map descriptor key -> raw per-axis array from velocity_description_
                descriptor_map = {
                    "mean": "mean",
                    "median": "median",
                    "mode": "mode",
                    "std": "standard_deviation",
                    "variance": "variance",
                    "range": "range",
                    "kurtosis": "kurtosis",
                    "skewness": "skewness",
                }

                for short_key, vd_key in descriptor_map.items():
                    raw = r.velocity_description[vd_key]
                    for i in range(n_dims):
                        axis = axis_labels[i] if i < len(axis_labels) else str(i)
                        val = raw[i]
                        # mode returns nested arrays (e.g. array([0.])); extract scalar
                        if hasattr(val, "__len__"):
                            val = val[0]
                        val = float(val)
                        # std=0 on a constant-velocity axis causes NaN in skewness/kurtosis
                        state["results"][n][f"vel_{short_key}_{axis}"] = (
                            "NaN" if (np.isnan(val) or np.isinf(val)) else val
                        )

            except Exception as e:
                errors.append(f"Trajectory {n + 1}: Velocity Description - {str(e)}")
                axis_labels = ["x", "y", "z"]
                for short_key in ["mean", "median", "mode", "std", "variance", "range", "kurtosis", "skewness"]:
                    for axis in axis_labels:
                        state["results"][n][f"vel_{short_key}_{axis}"] = "Error"

        if any("Frequency spectrum" in feature for feature in selected):
            try:
                axis_labels = ["x", "y", "z"]
                n_dims = r._r.shape[1] if r._r.ndim > 1 else 1

                # Per-axis frequency spectrum
                r.frequency_spectrum = r.frequency_spectrum_(r._r, r._t)
                for i in range(n_dims):
                    axis = axis_labels[i] if i < len(axis_labels) else str(i)
                    state["results"][n][f"dominant_frequency_{axis}"] = float(
                        r.frequency_spectrum["dominant frequency"][i]
                    )
                    state["results"][n][f"dominant_amplitude_{axis}"] = float(
                        r.frequency_spectrum["dominant amplitude"][i]
                    )

                # Euclidean norm |r(t)| — scalar signal representing distance from origin
                norm_r = np.linalg.norm(r._r, axis=1).reshape(-1, 1)
                r.frequency_spectrum_norm = r.frequency_spectrum_(norm_r, r._t)
                state["results"][n]["dominant_frequency_norm"] = float(
                    r.frequency_spectrum_norm["dominant frequency"][0]
                )
                state["results"][n]["dominant_amplitude_norm"] = float(
                    r.frequency_spectrum_norm["dominant amplitude"][0]
                )

            except Exception as e:
                errors.append(f"Trajectory {n + 1}: Frequency Spectrum - {str(e)}")
                axis_labels = ["x", "y", "z"]
                for axis in axis_labels:
                    state["results"][n][f"dominant_frequency_{axis}"] = "Error"
                    state["results"][n][f"dominant_amplitude_{axis}"] = "Error"
                state["results"][n]["dominant_frequency_norm"] = "Error"
                state["results"][n]["dominant_amplitude_norm"] = "Error"

        if any("Efficiency" in feature for feature in selected):
            try:
                r.efficiency = r.efficiency_(r._r)
                if np.isnan(r.efficiency) or np.isinf(r.efficiency):
                    state["results"][n]["efficiency"] = "NaN"
                else:
                    state["results"][n]["efficiency"] = r.efficiency
            except Exception as e:
                errors.append(f"Trajectory {n + 1}: Efficiency - {str(e)}")
                state["results"][n]["efficiency"] = "Error"

        if any("Diffusivity" in feature for feature in selected):
            try:
                r.velocity = r.velocity_(r._r, r._t)
                r.vacf = r.stationary_velocity_correlation_(r.velocity, r._t, np.arange(int(len(r.velocity))))
                r.diffusivity = r.green_kubo_(r.velocity, r._t, r.vacf)
                if np.isnan(r.diffusivity) or np.isinf(r.diffusivity):
                    state["results"][n]["diffusivity"] = "NaN"
                else:
                    state["results"][n]["diffusivity"] = r.diffusivity
            except Exception as e:
                errors.append(f"Trajectory {n + 1}: Diffusivity - {str(e)}")
                state["results"][n]["diffusivity"] = "Error"

        if any("Confinement" in feature for feature in selected):
            try:
                if not hasattr(r, "diffusivity") or (
                    hasattr(r, "diffusivity") and (np.isnan(r.diffusivity) or np.isinf(r.diffusivity))
                ):
                    r.velocity = r.velocity_(r._r, r._t)
                    r.vacf = r.stationary_velocity_correlation_(r.velocity, r._t, np.arange(int(len(r.velocity))))
                    r.diffusivity = r.green_kubo_(r.velocity, r._t, r.vacf)
                if not hasattr(r, "_r0"):
                    r.fractal_dimension, r._r0 = r.fractal_dimension_(r._r)
                r.confinement_probability = r.confinement_probability_(r._r0, r.diffusivity, r._t[-1])
                if np.isnan(r.confinement_probability) or np.isinf(r.confinement_probability):
                    state["results"][n]["confinement"] = "NaN"
                else:
                    state["results"][n]["confinement"] = r.confinement_probability
            except Exception as e:
                errors.append(f"Trajectory {n + 1}: Confinement - {str(e)}")
                state["results"][n]["confinement"] = "Error"

    if state["results"]:
        first = state["results"].get(0, {})
        lines = [f"{k}: {v}" for k, v in first.items()]
        result_text = "Results preview (only first trajectory):\n" + "\n".join(lines)

        if errors:
            result_text += f"\n\nWarnings/Errors ({len(errors)}):\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                result_text += f"\n... and {len(errors) - 5} more"

        result_box.set_text(result_text)
        save_btn.props(remove="disabled")
    else:
        result_box.set_text("No results produced!")


def show_about():
    with ui.dialog() as dialog, ui.card():
        ui.label("TrajPy GUI").style("font-weight: bold; font-size: 18px")

        # Try to show logo.png from same folder if it exists
        logo_path = os.path.join(os.path.dirname(__file__), "assets/logo.png")
        if os.path.exists(logo_path):
            img = Image.open(logo_path)
            img.thumbnail((400, 150))
            bio = BytesIO()
            img.save(bio, format="PNG")
            bio.seek(0)

            # Convert to base64 data URI
            img_base64 = base64.b64encode(bio.read()).decode("utf-8")
            img_src = f"data:image/png;base64,{img_base64}"
            ui.image(img_src).style("max-width: 100%")

        ui.label("Developed by Maurício Moreira-Soares")
        ui.link("phydev.github.io", "https://phydev.github.io")
        ui.label("trajpy@protonmail.ch")
        ui.button("Close", on_click=lambda: dialog.close())
    dialog.open()


def plot_trajectories(state: dict, plot_container, result_box):
    if not state["trajectories"]:
        result_box.set_text("Ingen trajectories å plotte")
        return

    fig = Figure(figsize=(10, 8))
    ax = fig.add_subplot(111)

    for n, trajectory in enumerate(state["trajectories"]):
        r = trajectory._r
        if r.shape[1] >= 2:  # 2D or 3D trajectory
            ax.plot(r[:, 0], r[:, 1], alpha=0.6, label=f"Trajectory {n + 1}")
            ax.scatter(r[0, 0], r[0, 1], marker="o", s=100, label=f"Start {n + 1}")
            ax.scatter(r[-1, 0], r[-1, 1], marker="s", s=100, label=f"End {n + 1}")

    ax.set_xlabel("X Position")
    ax.set_ylabel("Y Position")
    ax.set_title("Trajectories")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Save to BytesIO and convert to base64 data URI
    bio = BytesIO()
    fig.savefig(bio, format="png", dpi=100, bbox_inches="tight")
    bio.seek(0)

    # Convert to base64 data URI
    img_base64 = base64.b64encode(bio.read()).decode("utf-8")
    img_src = f"data:image/png;base64,{img_base64}"

    # Clear previous plot if exists
    plot_container.clear()
    with plot_container:
        ui.image(img_src).style("max-width: 30%")

    plt.close(fig)


def save_results(state: dict, result_box):
    if not state["results"]:
        result_box.set_text("No results to save")
        return

    # Create CSV from state['results']
    header = []
    rows = []
    for n in sorted(state["results"].keys()):
        entries = state["results"][n]
        if not header:
            header = list(entries.keys())
        rows.append([entries.get(h, "") for h in header])

    csv_lines = [",".join(header)]
    for row in rows:
        csv_lines.append(",".join(map(str, row)))
    csv_data = "\n".join(csv_lines)

    # Create download link
    csv_bytes = csv_data.encode("utf-8")
    csv_base64 = base64.b64encode(csv_bytes).decode("utf-8")

    # Trigger download using JavaScript
    ui.run_javascript(f"""
        const link = document.createElement('a');
        link.href = 'data:text/csv;base64,{csv_base64}';
        link.download = 'trajpy_results.csv';
        link.click();
    """)

    result_box.set_text("Results downloaded as trajpy_results.csv")
