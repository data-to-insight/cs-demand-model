import logging

from prpc_python import RpcApp

from cs_demand_model.rpc import views
from cs_demand_model.rpc.state import DemandModellingState
from cs_demand_model.rpc.util import json_response

log = logging.getLogger(__name__)


class T2DemandModellingSession:
    def __init__(self):
        self.state = DemandModellingState()
        self.views = {
            "datastore": views.DataStoreView(),
            "charts": views.ChartsView(),
        }

    @property
    def current_view(self):
        if self.state.datastore is None:
            return self.views["datastore"]
        else:
            return self.views["charts"]

    def action(self, action, data=None):
        print("Action:", action, data)
        if action != "init":
            self.state = self.current_view.action(action, self.state, data)

        return dict(
            view=self.current_view.render(self.state),
            state=dict(
                start_date=self.state.start_date,
                end_date=self.state.end_date,
                prediction_start_date=self.state.prediction_start_date,
                prediction_end_date=self.state.prediction_end_date,
                step_size=self.state.step_days,
                files=self.state.files,
                chart_filter=self.state.chart_filter,
                **self.state.costs,
                **self.state.cost_proportions,
                **self.state.adjustments,
            ),
            errors=self.state.errors,
        )


app = RpcApp("CS Demand Model")
dm_session = T2DemandModellingSession()


@app.call
def reset():
    global dm_session
    dm_session = T2DemandModellingSession()


@app.call
def action(action, data=None):
    try:
        return json_response(dm_session.action(action, data))
    except Exception as e:
        log.exception("Error handling action")
        raise e
