# Children's Social Care Demand Model

This is the Python implementation of the Children's Social Care Demand Model.

It can be used as a library, as a command line tool, or as part of a web application. 

It is designed to be used within Pyodide and has a partnering front-end application here: 

https://github.com/SocialFinanceDigitalLabs/csdmpy-frontend

## Principles

The model is designed to run of the SSDA903 returns, and requires several years' worth of 
data to be able to build a model for the system behaviour. 

Model components:

* [Configuration](./docs/configuration.ipynb) - How to configure the tool
* [File Loader](./docs/file-loader.ipynb) - How to load files into the tool
* [Data Container](./docs/data-container.ipynb) - How we enrich and access the data from the model
* [Data Analysis](./docs/data-analysis.ipynb) - The key calculations required by the predictive model
* Predictor - takes the model and uses it to predict the number of children in care at a given point in time.

The components are designed to be re-usable and extensible. 

In addition there are a couple of abstraction layers to handle loading of files in different environments. 

## Quickstart

Want to get started straight away? You can install from the GitHub repo and run from the command line:

```bash

pip install 'git+https://github.com/SocialFinanceDigitalLabs/csdm-py#egg=csdmpy[cli]'

```

The part after the # is optional, but will install a few extra dependencies to make the experience better when 
running from the command line.

You can now view the command line options by running:

```bash
python -m csdmpy
````

For example, you can run a quick predictive model using a sample dataset with:

```bash
python -m csdmpy predict sample://v1.zip
```

In this case we have used a sample dataset, but you can also use a local folder by specifying the path to the folder:

```bash
python -m csdmpy predict path/to/my/folder
```

The folder currently needs to have quite a specific structure with sub-folders for each year. You can make
sure your folder is read correctly by running:

```bash
 python -m csdmpy list-files sample://v1.zip 
```
(obviously replacing the path with your own)

You can get more information about passing options to the command line tool by adding `--help` after the command, e.g.

```bash
python -m csdmpy analyse --help
```
