import geopandas as gpd
import matplotlib.pyplot as plt

density = gpd.read_file("outputs/reseeding_map.gpkg", layer="density")
density.plot(column="gap_status", legend=True, figsize=(8, 8))
plt.savefig("quick_check.png")