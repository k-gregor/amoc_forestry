This is the code accompanying the paper "Robust tree portfolios hedge European forestry against AMOC tipping risk" by Gregor et al. (in revision)


This repository runs standalone with the data provided in the `data` directory. Note, however, that it contains only a subset of the original data (every 100th row).
This allows reproducing all the figures on a laptop. Those figures will look very similar to the ones in the paper.
To run the optimization on the entire dataset, one would need access to a machine with more RAM, ideally a supercomputer.

- optimization_plots.ipynb takes the optimized data and plots them across the continent.
- input_data