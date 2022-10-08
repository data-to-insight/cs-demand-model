# Children's Social Care Demand Model

This is the Python implementation of the Children's Social Care Demand Model.

It can be used as a library, as a command line tool, or as part of a web application. 

It is designed to be used within Pyodide and has a partnering front-end application here: 

https://github.com/SocialFinanceDigitalLabs/csdmpy-frontend

## Principles

The model is designed to run of the SSDA903 returns, and requires several years' worth of 
data to be able to build a model for the system behaviour. 

Model components:

* Ingest - takes the SSDA903 files and converts it to a longitudinal dataset surfacing at the experience of individual children.
* Model - takes the longitudinal dataset and builds a statistical model of the system behaviour.
* Predictor - takes the model and uses it to predict the number of children in care at a given point in time.

The components are designed to be re-usable and extensible. 

In addition there are a couple of abstraction layers to handle loading of files in different environments. 

## Components

Let's look at each of the components in more detail. The first problem is to load
data. The data is in the form of SSDA903 files, which are a set of tabular files 
for each reporting year. We currently only support CSV files, but the API
is designed to be easily extensible to other file formats.


### File handling

File handing belongs in the `csdmpy.datastore` module. 
The key part of this is the `DataStore` class, which 
has methods for iterating over the set of provided files, 
and to open those files. It also has a method to load the data as
a dataframe, but this doesn't seem right so is likely to change. 

The purpose of this library is to make sure we can consistently
load data in different environments. The most important of which is
to pass on any required metadata about the files. However,
as mentioned, I'm not sure the metadata is that important, so
there may be additional scope for improvement.

The important thing is that the different files for each year is combined correctly,
so we need to know the year of each file. How to provide this information depends
on the datastore implementation.

TODO: Review the datastore API

### Data Container

The purpose of the data container is to merge the different files to
create a consolidated system view. The data container merges the
individual tables, deduplicates the data, and then adds categories
used for the statistical model. 

Most importantly it calculates child ages, and groups these into age 
categories as defined by `AgeBracket`. This is currently an enum, but
in future this may be user configurable. 

The enrichment process also looks at the placement types and categorises
these according to the `PlacementType` enum, as well as a 
NOT_IN_CARE category that children can move in and out of.

TODO: Add Jupyter notebook showing the data container in action and
explaining the transitions.

### Model

The model is a statistical model that is built from the data container.

### Predictor

The predictor uses the model to predict the number of children in care

## Usage

The model can be used as a library, as a command line tool,
or as part of the webapp.





'