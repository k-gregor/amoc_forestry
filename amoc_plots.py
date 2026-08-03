import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib as mpl
import numpy as np
from collections import defaultdict
from matplotlib.colors import to_rgb
from matplotlib.patches import Patch
import geopandas
import cartopy.crs as ccrs
from cartopy.io import shapereader
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


SSS = 0.1

countries_polygons = geopandas.read_file(shapereader.natural_earth(resolution='10m', category='cultural', name='admin_0_countries'))

pink = np.array([1.0, 0.4, 0.7, 1.0])  # RGBA for pink



def make_viridis_pink(vmin=-4, vmax=100, pink_upper=0.0001, n_viridis=254):
    """Colormap/norm pair that is flat pink over [vmin, pink_upper] and
    viridis over (pink_upper, vmax]. Uses BoundaryNorm so the pink/viridis
    boundary sits exactly at pink_upper regardless of vmax (a plain
    Normalize + a default-resolution LinearSegmentedColormap would round
    the boundary to the nearest of its 256 LUT steps, i.e. off by up to
    (vmax-vmin)/256 - noticeable for a narrow pink band). cmap and norm
    must always be used together since the boundary is baked into both."""
    viridis_colors = plt.cm.viridis(np.linspace(0, 1, n_viridis))
    colors = np.vstack([pink, viridis_colors])
    cmap = mcolors.ListedColormap(colors)
    bounds = [vmin, pink_upper] + list(np.linspace(pink_upper, vmax, n_viridis + 1))[1:]
    norm = mcolors.BoundaryNorm(bounds, ncolors=len(colors))
    return cmap, norm


viridis_pink, viridis_pink_norm = make_viridis_pink(vmax=100)
viridis_pink_50, viridis_pink_norm_50 = make_viridis_pink(vmax=50)
viridis_pink_15, viridis_pink_norm_15 = make_viridis_pink(vmax=15)


blues = plt.cm.get_cmap('Blues', 256)
blues_colors = blues(np.linspace(0, 1, 256))
blues_colors[0] = pink
blues_pink = mcolors.ListedColormap(blues_colors)
blues_pink_norm_15 = mcolors.Normalize(vmin=0, vmax=15)

colors = ['red', 'darkorange', 'gold', 'dodgerblue', 'blue']
bounds = [0, 0.0001, 5, 10, 30, 100]  # very small gap to distinguish 0 exactly
prob_cmap = mcolors.ListedColormap(colors)
prob_norm = mcolors.BoundaryNorm(boundaries=bounds, ncolors=len(colors))

# continuous version of prob_cmap: same colors, anchored at the same bounds,
# but interpolated smoothly instead of stepped
prob_cmap_cont = mcolors.LinearSegmentedColormap.from_list(
    'prob_cmap_cont',
    list(zip([b / bounds[-1] for b in bounds], colors + [colors[-1]]))
)
prob_norm_cont = mcolors.Normalize(vmin=bounds[0], vmax=bounds[-1])

europe_extent = [-12, 32, 35, 73]


species_to_color = {
    'Abies_alba': '#9e9ac8',
    'Acer_campestre': '#a55194',
    'Acer_pseudoplatanus': '#ce6dbd',
    'Alnus_glutinosa': '#969696',
    'Alnus_incana': '#bdbdbd',
    'Betula_pendula': '#bd9e39',
    'Betula_pubescens': '#e7ba52',
    'Carpinus_betulus': '#31a354',
    'Corylus_avellana': '#a1d99b',
    'Fagus_sylvatica': '#000000',
    'Fraxinus_excelsior': '#de9ed6',
    'Picea_abies': '#756bb1',
    'Pinus_halepensis': '#3182bd',
    'Pinus_nigra': '#6baed6',
    'Pinus_pinaster': '#9ecae1',
    'Pinus_sylvestris': '#c6dbef',
    'Populus_tremula': '#393b79',
    'Prunus_avium': '#637939',
    'Quercus_ilex': '#843c39',
    'Quercus_petraea': '#e6550d',
    'Quercus_pubescens': '#fd8d3c',
    'Quercus_robur': '#fdae6b',
    'Quercus_suber': '#fdd0a2',
    'Sorbus_aucuparia': '#b20000',
}


def plot_present_historical_single_portfolio(occurrences, projections, filename):
    fig, ax = plt.subplots(1, 4, figsize=(24, 6), subplot_kw={'projection': ccrs.PlateCarree()})

    s = 0.1

    cmap = prob_cmap
    norm = prob_norm

    sc0 = occurrences.plot.scatter(
        x='lon', y='lat', c='occurring_species_suitability_present', s=s,
        cmap=cmap, norm=norm, ax=ax[0], colorbar=False, rasterized=True, marker='s'
    )

    sc1 = occurrences.plot.scatter(
        x='lon', y='lat', c='future_min_suitability', s=s,
        cmap=cmap, norm=norm, ax=ax[1], colorbar=False, rasterized=True, marker='s'
    )
    sc2 = projections.plot.scatter(
        x='x', y='y', c='opt_single_species_min_prob', s=s,
        cmap=cmap, norm=norm, ax=ax[2], colorbar=False, rasterized=True, marker='s'
    )
    sc3 = projections.plot.scatter(
        x='x', y='y', c='opt_portfolio_min_prob', s=s,
        cmap=cmap, norm=norm, ax=ax[3], colorbar=False, rasterized=True, marker='s'
    )

    ax[0].set_title('Present day\nmaximum suitability', fontsize=14)
    ax[1].set_title('Minimal future suitability\nof best-suited present day species', fontsize=14)
    ax[2].set_title('Minimal future suitability\nof single best species', fontsize=14)
    ax[3].set_title('Minimal future suitability\nof portfolio', fontsize=14)

    for idx, letter in enumerate(['a', 'b', 'c', 'd']):
        ax[idx].text(0.1, 0.9, letter + ')', fontsize=15, weight='bold',
                     va='top', ha='right', transform=ax[idx].transAxes)
        ax[idx].add_geometries(
            countries_polygons['geometry'], crs=ccrs.PlateCarree(),
            facecolor='none', edgecolor='0.2', linewidth=0.5
        )
        ax[idx].set_extent(europe_extent, crs=ccrs.PlateCarree())
        ax[idx].set_ylabel('Lat')
        ax[idx].set_xlabel('Lon')
        ax[idx].set_xticks([-10, 0, 10, 20, 30], crs=ccrs.PlateCarree())
        ax[idx].set_yticks([35, 45, 55, 65], crs=ccrs.PlateCarree())
        ax[idx].xaxis.set_major_formatter(LONGITUDE_FORMATTER)
        ax[idx].yaxis.set_major_formatter(LATITUDE_FORMATTER)


    sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm._A = []  # required for older matplotlib versions

    cbar_ax = fig.add_axes([0.92, 0.2, 0.01, 0.6])
    cbar = fig.colorbar(sm, cax=cbar_ax)
    cbar.set_label('Suitability')

    plt.subplots_adjust(right=0.9)

    cbar.set_ticks([0.00005, 0.0001, 5, 10, 30, 100])
    cbar.set_ticklabels(['0', '>0', '5', '10', '30', '100'])

    if filename:
        fig.savefig(filename, dpi=300, bbox_inches='tight')


def plot_single_vs_portfolio(df_final_optimized, titleaddition='', filename=''):
    fig, ax = plt.subplots(1, 3, figsize=(18, 5), subplot_kw={'projection': ccrs.PlateCarree()})

    alpha = 1.0

    sc0 = ax[0].scatter(df_final_optimized['x'], df_final_optimized['y'], alpha=alpha, c = df_final_optimized['opt_single_species_min_prob'], cmap=viridis_pink_50, norm=viridis_pink_norm_50, s=SSS)
    ax[0].set_title('Single best species', fontsize=16)
    sc1 = ax[1].scatter(df_final_optimized['x'], df_final_optimized['y'], alpha=alpha, c = df_final_optimized['opt_portfolio_min_prob'], cmap=viridis_pink_50, norm=viridis_pink_norm_50, s=SSS)
    ax[1].set_title('Portfolio', fontsize=16)
    sc2 = ax[2].scatter(df_final_optimized['x'], df_final_optimized['y'], alpha=alpha, c = df_final_optimized['opt_portfolio_min_prob'] - df_final_optimized['opt_single_species_min_prob'], cmap = 'seismic_r', vmin=-30, vmax=30, s=SSS)
    ax[2].set_title('Diff (Portfolio-Single)', fontsize=16)

    for axxx in [ax[0], ax[1]]:
        cbar1 = fig.colorbar(sc0, ax=axxx, label='Suitability (%)', shrink=0.8, spacing='proportional')
        cbar1.set_ticks([-2, 0, 10, 20, 30, 40, 50])
        cbar1.set_ticklabels(['0', '>0', '10', '20', '30', '40', '50'])
        cbar1.ax.minorticks_off()

    fig.colorbar(sc2, ax=ax[2], label='Difference in suitability (%-points)', shrink=0.8)

    for idx in range(len(ax)):
        label = f"{chr(97 + idx)})"  # chr(97) = 'a'
        ax[idx].text(
            0.1, 0.9,                # X,Y position in axes coords (adjust as needed)
            label,
            transform=ax[idx].transAxes, # Use axes coords
            fontsize=14,
            fontweight='bold',
            ha='left', va='top'
        )
        ax[idx].add_geometries(
            countries_polygons['geometry'], crs=ccrs.PlateCarree(),
            facecolor='none', edgecolor='0.2', linewidth=0.5
        )
        ax[idx].set_extent(europe_extent, crs=ccrs.PlateCarree())
        ax[idx].set_ylabel('Lat')
        ax[idx].set_xlabel('Lon')
        ax[idx].set_xticks([-10, 0, 10, 20, 30], crs=ccrs.PlateCarree())
        ax[idx].set_yticks([35, 45, 55, 65], crs=ccrs.PlateCarree())

        ax[idx].xaxis.set_major_formatter(LONGITUDE_FORMATTER)
        ax[idx].yaxis.set_major_formatter(LATITUDE_FORMATTER)

    fig.tight_layout()

    if filename:
        fig.savefig(filename, dpi=300, bbox_inches='tight')


def plot_n_species_of_portfolio(df, filename=''):
    fig, ax = plt.subplots(1, 2, figsize=(16, 8), subplot_kw={'projection': ccrs.PlateCarree()})

    fontsize = 16

    df['n_species_in_pf'] = df['opt_portfolio'].map(lambda x: len(x.keys()))

    vmax = df['n_species_in_pf'].max()
    vmin = 1

    boundaries = np.arange(vmin - 0.5, vmax + 1.5, 1)
    pf_norm = mcolors.Normalize(vmin=vmin, vmax=vmax)


    ax[0].scatter(df['x'], df['y'], c = df['n_species_in_pf'], s=SSS, cmap='Blues', norm=pf_norm)
    ax[0].set_title('Number of species in portfolio', fontsize=fontsize)

    cbar = fig.colorbar(
        mpl.cm.ScalarMappable(cmap='Blues', norm=pf_norm),
        ax=ax[0],
        boundaries=boundaries,
        orientation='vertical',
        fraction=0.02,
        pad=0.04
    )
    cbar.set_label('Number of Species')
    tick_values = np.arange(vmin, vmax+1, 1)
    cbar.set_ticks(tick_values)


    # to get plots in 20% steps
    diversity_step = 0.2
    diversity_factor = 1.0/diversity_step

    df['portfolio_top_share'] = df['opt_portfolio'].map(lambda portfolio: sorted(portfolio.items(), key=lambda item: item[1], reverse=True)[0][1])
    df['portfolio_top_share_rounded'] = df['portfolio_top_share'].map(lambda val: np.floor(diversity_factor*val)/diversity_factor) + 0.1

    boundaries2 = np.arange(0, 1.21, diversity_step)
    pf_norm2 = mcolors.Normalize(vmin=0, vmax=1)

    ax[1].scatter(df['x'], df['y'], c = df['portfolio_top_share_rounded'], s=1, cmap='inferno', norm=pf_norm2)
    ax[1].set_title('Share of top species in portfolio', fontsize=fontsize)
    cbar = fig.colorbar(
        mpl.cm.ScalarMappable(cmap='inferno', norm=pf_norm2),
        ax=ax[1],
        boundaries=boundaries2,
        orientation='vertical',
        fraction=0.02,
        pad=0.04
    )
    cbar.set_label('Share')
    tick_values = np.arange(diversity_step/2.0, 1.21, diversity_step)
    cbar.set_ticks(tick_values)
    cbar.set_ticklabels([f'{100*(tick-diversity_step/2):.0f}-{100*(tick+diversity_step/2):.0f}%' if tick < 1 else '100%' for tick in tick_values])


    for idx in range(len(ax)):
        label = f"{chr(97 + idx)})"  # chr(97) = 'a'
        ax[idx].text(
            0.1, 0.9,                # X,Y position in axes coords (adjust as needed)
            label,
            transform=ax[idx].transAxes, # Use axes coords
            fontsize=14,
            fontweight='bold',
            ha='left', va='top'
        )
        ax[idx].add_geometries(
            countries_polygons['geometry'], crs=ccrs.PlateCarree(),
            facecolor='none', edgecolor='0.2', linewidth=0.5
        )
        ax[idx].set_extent(europe_extent, crs=ccrs.PlateCarree())
        ax[idx].set_ylabel('Lat')
        ax[idx].set_xlabel('Lon')
        ax[idx].set_xticks([-10, 0, 10, 20, 30], crs=ccrs.PlateCarree())
        ax[idx].set_yticks([35, 45, 55, 65], crs=ccrs.PlateCarree())

        ax[idx].xaxis.set_major_formatter(LONGITUDE_FORMATTER)
        ax[idx].yaxis.set_major_formatter(LATITUDE_FORMATTER)


    if filename:
        fig.savefig(filename, dpi=300, bbox_inches='tight')


def plot_single_best_species(ax, df_final_optimized, species_list, s=1, filename=None, title='Single best species', column='opt_single_species', colorbar=True):

    df_final_optimized['species_color'] = df_final_optimized[column].map(lambda sp: species_to_color[species_list[int(sp)]])

    ax.scatter(df_final_optimized['x'], df_final_optimized['y'], alpha=1.0, c = df_final_optimized['species_color'], s=s)
    ax.set_title(title)


    ax.set_extent(europe_extent, crs=ccrs.PlateCarree())
    ax.add_geometries(
        countries_polygons['geometry'], crs=ccrs.PlateCarree(),
        facecolor='none', edgecolor='0.2', linewidth=0.5
    )
    ax.set_extent(europe_extent, crs=ccrs.PlateCarree())


def plot_species_scenarios(df_final, species_list=None, scenarios=None, s=1, alpha=0.8, cmap='viridis', vmin=0, vmax=50):
    df = df_final.reset_index()

    for species in species_list:
        fig, axes = plt.subplots(1, len(scenarios), figsize=(3 * len(scenarios), 3), sharex=True, sharey=True)
        fig.suptitle(species, fontsize=16)

        if len(scenarios) == 1:
            axes = [axes]  # make iterable

        sc = None
        for i, scenario in enumerate(scenarios):
            col_name = f"{species}-{scenario}"
            if col_name not in df.columns:
                print(f"Warning: {col_name} not found in DataFrame columns.")
                continue

            sc = axes[i].scatter(
                df['x'], df['y'],
                c=df[col_name],
                s=s,
                alpha=alpha,
                cmap=prob_cmap,
                norm=prob_norm,
            )
            axes[i].set_title(scenario)
            axes[i].set_xlabel('x')
            if i == 0:
                axes[i].set_ylabel('y')


        cbar_ax = fig.add_axes([0.93, 0.2, 0.02, 0.6])
        fig.colorbar(sc, cax=cbar_ax, fraction=0.02, pad=0.04).set_label('Prob')

        plt.subplots_adjust(top=0.9)  # Make space for suptitle
        plt.show()