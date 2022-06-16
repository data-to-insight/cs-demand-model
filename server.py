from dateutil.parser import parse
from flask import Flask, request, render_template

from csdmpy.api import ApiSession
from csdmpy.config import age_brackets as bin_defs
from csdmpy.utils import ezfiles

app = Flask(__name__)

session = ApiSession(ezfiles())


def _request_date(value, default=None):
    return parse(request.args.get(value, default))

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calc')
def calculate_model():
    model_params = {
        'history_start': _request_date('history_start', '2015-01-01'),
        'reference_start': _request_date('reference_start', '2016-06-01'),
        'reference_end': _request_date('reference_end', '2017-06-01'),
        'history_end': _request_date('history_end', '2019-01-01'),
        'prediction_end': _request_date('prediction_end', '2025-01-01'),
        'step_size': '4m',
        'bin_defs': bin_defs
    }

    adjustments = [{'age_bracket': '10 to 16', 'from': 'Foster', 'to': 'Resi', 'n': 0, 'id': 100},
                   {'age_bracket': '10 to 16', 'from': 'Foster', 'to': 'Other', 'n': 10, 'id': 101}]

    session.calculate_model(model_params, adjustments)

    return dict(
        base_pop_graph=session.model.base_pop_graph,
        adj_pop_graph=session.model.adj_pop_graph,
    )

def caclulate_costs():
    base_costs = {'Foster': {'friend_relative': 10, 'in_house': 20, 'IFA': 30, },
                  'Resi': {'in_house1': 40, 'external': 60},
                  'Supported': {'Sup': 40, },
                  'Other': {'secure_home': 150, 'with_family': 30, 'any_other': 40}}

    cost_dict = {'base': base_costs}  # , 'adjusted': adjusted_costs}

    proportions = {'Foster': {'friend_relative': 0.5, 'in_house': 0.2, 'IFA': 0.3, },
                   'Resi': {'in_house1': 0.4, 'external': 0.6},
                   'Supported': {'Sup': 1, },
                   'Other': {'secure_home': 0.7, 'with_family': 0.1, 'any_other': 0.2}}


if __name__ == "__main__":
    app.run(debug=True)
