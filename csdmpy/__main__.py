from datetime import date

import click
import pandas as pd

from csdmpy import DemandModellingDataContainer, ModelFactory, PopulationStats
from csdmpy.config import Config
from csdmpy.datastore import fs_datastore

try:
    import matplotlib.pyplot as pp
except ImportError:
    pp = None


def plot_option(*args, help=None, **kwargs):
    if not pp:
        help = "Requires matplotlib"
    return click.option(*args, help=help, **kwargs)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("source")
def list_files(source: str):
    """
    Opens SOURCE and lists the available files and metadata. This is for testing of source folders.
    """
    ds = fs_datastore(source)
    files = sorted(ds.files, key=lambda x: (x.metadata.year, x.metadata.name))
    for file in files:
        click.secho(f"{file.name}", fg="green", bold=True)
        click.secho(f"  Year: {click.style(file.metadata.year, fg='blue')}")
        if file.metadata.table:
            click.secho(f"  Table: {click.style(file.metadata.table, fg='blue')}")
        else:
            click.secho(f"  Table: {click.style('UNKNOWN', fg='red')}")
        click.secho(f"  Size: {click.style(file.metadata.size, fg='blue')}")
        click.echo()


@cli.command()
@click.argument("source")
@click.argument("start", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.argument("end", type=click.DateTime(formats=["%Y-%m-%d"]))
def extract(source: str, start: date, end: date):
    """
    Opens SOURCE and runs analysis on the data between START and END. SOURCE can be a file or a filesystem URL.
    """
    config = Config()
    datastore = fs_datastore(source)
    dc = DemandModellingDataContainer(datastore, config)
    stats = PopulationStats(dc.get_enriched_view(), config)
    click.echo(stats.transition_rates(start, end))


@cli.command()
@click.argument("source")
@click.argument("start", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.argument("end", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.argument("prediction_date", type=click.DateTime(formats=["%Y-%m-%d"]))
@plot_option("--plot", "-p", is_flag=True, help="Plot the results")
def predict(source: str, start: date, end: date, prediction_date: date, plot: bool):
    config = Config()
    datastore = fs_datastore(source)
    dc = DemandModellingDataContainer(datastore, config)
    stats = PopulationStats(dc.get_enriched_view(), config)
    fac = ModelFactory(stats, start, end)
    predictor = fac.predictor(end)
    prediction_days = (prediction_date - end).days
    predicted_pop = predictor.predict(prediction_days, progress=True)

    click.echo(predicted_pop)

    if plot:
        if not pp:
            click.secho("Plotting requires matplotlib", fg="red")
        else:
            historic_pop = stats.stock.loc[:end]

            pd.concat([historic_pop, predicted_pop], axis=0).plot()
            pp.axvline(end, alpha=0.4)
            pp.axvspan(start, end, alpha=0.1)
            pp.show()


if __name__ == "__main__":
    cli()
