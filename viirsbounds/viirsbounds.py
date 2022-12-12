#!/usr/bin/env python3

import geojson
from pathlib import Path
import h5py
import numpy as np

import typer
app = typer.Typer()


TAG2GROUP = {'GDNBO':'VIIRS-DNB-GEO_All',
             'GIMGO':'VIIRS-IMG-GEO_All',
             'GMODO':'VIIRS-MOD-GEO_All',
             'GMTCO':'VIIRS-MOD-GEO-TC_All',
             'GIMGO':'VIIRS-IMG-GEO_All',
             'GITCO':'VIIRS-IMG-GEO-TC_All',}

def geo_group_from_filename(filename:Path):
    for key in TAG2GROUP.keys():
        if key in filename.stem:
            return TAG2GROUP[key]
    raise RuntimeError

def bounded_polygon_from_dataset(ds, stride:int):
    # get bounding polygon via something like:
    # I believe order of operations here is important for it to go around in a rectangle
    # longitude[0,:]
    # longitude[:,-1]
    # longitude[-1,:]
    # longitude[:,0]
    strided = np.concatenate(( ds[0,::stride],
                               ds[::stride,-1],
                               ds[-1,::stride],
                               ds[::stride,0] ))
    return strided


def main(geolocation_file:Path = typer.Argument(
                                     ...,
                                     exists=True,
                                     file_okay=True,
                                     dir_okay=False,
                                     readable=True,
                                     resolve_path=True,
                                 ),
         stride_by:int = typer.Option(default=16)
        ):

    print(f"Geolocation file: {geolocation_file}")
    geogroup = geo_group_from_filename(geolocation_file)

    f = h5py.File(geolocation_file, 'r')

    dslat = f[f"All_Data/{geogroup}/Latitude"]
    dslon = f[f"All_Data/{geogroup}/Longitude"] # shape like (768, 3200)
#    lat_strided = dslat[0::stride_by,0::stride_by]
#    lon_strided = dslon[0::stride_by,0::stride_by] # shape like (48, 200)
    lat_polygon = bounded_polygon_from_dataset(dslat, stride=stride_by)
    lon_polygon = bounded_polygon_from_dataset(dslon, stride=stride_by)

    # a.astype(float) fixes geojson not knowing about numpy types, otherwise: "ValueError: -79.11869 is not a JSON compliant number"
    coords = zip(lon_polygon.astype(float), lat_polygon.astype(float))
    polygon = geojson.Polygon(coords)

    geojson_filename = geolocation_file.name.replace('.h5', f".stride{stride_by}.json")
    with open(geojson_filename, 'w') as geojson_file:
        geojson_file.write(geojson.dumps(polygon))

    print(f"GeoJSON output: {geojson_filename}")
    del f

if __name__ == "__main__":
    typer.run(main)