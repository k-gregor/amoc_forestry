This is the code accompanying the paper "Robust tree portfolios hedge European forestry against AMOC tipping risk" by Gregor et al. (2026)

This repository runs standalone with the data provided in the `data` directory. Note, however, that it contains only a subset of the original data (every 100th row).
This allows running the optimization and reproducing all the figures on a laptop. Those figures will look very similar to the ones in the paper.
To run the optimization on the entire dataset, one would need access to a machine with more RAM, ideally a supercomputer.

- input_data.ipynb: shows different statistics about the input data (species suitabilities)
- optimization.ipynb: runs the optimization and stores it (not needed to plot the figures, as an optimized dataset is provided within this repo already)
- optimization_plots.ipynb takes the optimized data and plots them across the continent.