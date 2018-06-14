# `conda-build` metadata and scripts
Each folder contains `meta.yaml` and `build.sh` necessary to build 
anaconda packages.

To build a package and install it from local repository to your virtual 
environment run:
```
conda-build .
conda install -n ull3 link-grammar-minisat-bundled --use-local

``` 
Replace `-n ull3` with the name of your virtual environment.