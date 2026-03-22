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


STATE = {
    "uploaded_files": [],  # liste av (filename, bytes)
    "trajectories": [],  # liste av tj.Trajectory-objekter
    "selected_features": set(),
    "results": {},
    "last_saved_path": None,
}
