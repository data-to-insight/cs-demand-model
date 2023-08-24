# Children's Social Care Demand Model

[![Binder](https://mybinder.org/badge_logo.svg)][launch]

This is the Python implementation of the Children's Social Care Demand Model.

It can be used as a library, as a command line tool, or as part of a web application. 

It can also be used within Pyodide and has a partnering front-end application here: 

https://github.com/data-to-insight/cs-demand-model-web

## Principles

The model is designed to run of the SSDA903 returns, and requires several years' worth of 
data to be able to build a model for the system behaviour. 

Model components:

* [Configuration](./docs/configuration.ipynb) - How to configure the tool
* [File Loader](./docs/file-loader.ipynb) - How to load files into the tool
* [Data Container](./docs/data-container.ipynb) - How we enrich and access the data from the model
* [Data Analysis](./docs/data-analysis.ipynb) - The key calculations required by the predictive model
* [Predictor](./docs/predict.ipynb) - takes the model and uses it to predict the number of children in care at a given point in time.

The components are designed to be re-usable and extensible. 

In addition there are a couple of abstraction layers to handle loading of files in different environments. 

## Quickstart

Want to get started straight away? You can install from the GitHub repo and run from the command line:

```bash

pip install 'cs-demand-model[cli]'

```

The part after the # is optional, but will install a few extra dependencies to make the experience better when 
running from the command line.

You can now view the command line options by running:

```bash
demand-model
````

For example, you can run a quick predictive model using a sample dataset with:

```bash
demand-model predict sample://v1.zip
```

In this case we have used a sample dataset, but you can also use a local folder by specifying the path to the folder:

```bash
demand-model predict path/to/my/folder
```

The folder currently needs to have quite a specific structure with sub-folders for each year. You can make
sure your folder is read correctly by running:

```bash
 demand-model list-files sample://v1.zip 
```
(obviously replacing the path with your own)

You can get more information about passing options to the command line tool by adding `--help` after the command, e.g.

```bash
demand-model analyse --help
```

## Launching with Jupyter

You can also launch the model with Jupyter. Install the library with the jupyter extension:

```bash 
pip install 'cs-demand-model[jupyter]'
```

Then launch Jupyter:

```bash
jupyter-lab
```
(or `jupyter notebook` if you prefer)

## Launching on Binder

You can also launch the model on [Binder][binder]. 
[Click to launch][launch] the [sample repository][sample-repo] on binder.


[launch]: https://mybinder.org/v2/gh/SocialFinanceDigitalLabs/cs-demand-model-binder/HEAD?labpath=start-here.ipynb
[binder]: https://mybinder.org
[sample-repo]: https://github.com/SocialFinanceDigitalLabs/cs-demand-model-binder

https://mybinder.org/v2/gh/SocialFinanceDigitalLabs/cs-demand-model-binder/HEAD?labpath=start-here.ipynb
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/SocialFinanceDigitalLabs/cs-demand-model-binder/HEAD?labpath=start-here.ipynb)