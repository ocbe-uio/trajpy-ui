# TrajPy User Interface

## Overview
TrajPy GUI is a graphical interface for analyzing particle trajectories using the TrajPy library. It allows you to upload trajectory files, visualize them, compute various physical features, and export results.
Getting Started

1. **Upload Trajectory Files**
- Click "Upload one or several files (CSV or YAML)"
- Select one or multiple files:
    - CSV files: Should contain trajectory coordinates (skip first line as header)
    - YAML files: LAMMPS dump format supported
- Multiple files can be uploaded sequentially (they accumulate)
- Status shows total files and trajectories loaded

2. **Visualize Trajectories**

- Click "Plot Trajectories" to display all loaded trajectories
- The plot shows:
    - Trajectory paths in different colors
    - Start points (circles)
    - End points (squares)
    - Legend identifying each trajectory
  
3. **Select Features to Compute**
- Choose from the following analysis features:
    - Anomalous Exponent: Characterizes diffusion type (α)
    - MSD Ratio: Mean Square Displacement ratio
    - Fractal dimension: Self-similarity measure 
    - Anisotropy & Kurtosis: Shape and directional properties 
    - Straightness: Path linearity 
    - Efficiency: Direct vs. actual path ratio 
    - Gaussianity: Displacement distribution normality 
    - Diffusivity: Diffusion coefficient 
    - Confinement Prob.: Probability of confined motion

4. **Compute Results**
- Select desired features using checkboxes
- Click "Compute!"
- Results for the first trajectory appear in the status area
- Warnings/errors are displayed if computation fails for any trajectory

5. **Save Results**
Click "Save results (CSV)" after computation
A CSV file (trajpy_results.csv) downloads automatically
Contains computed features for all trajectories

6. **About**
Click "About" for version information and contact details

## Tips
- Upload files incrementally to analyze multiple datasets together
- NaN/Error values indicate computation issues for specific features
- Plot trajectories before computing to verify data loaded correctly