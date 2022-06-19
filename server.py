#!/usr/bin/env python
from base64 import b64encode

from dateutil.parser import parse
from flask import Flask, request, render_template
from flask_cors import CORS

from csdmpy.api import ApiSession
from csdmpy.classy import ModelParams
from csdmpy.utils import ezfiles

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

session = ApiSession(ezfiles())


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calc', methods=['POST'])
def calculate_model():
    model_params = ModelParams.Schema().load(request.form)
    #
    # adjustments = [{'age_bracket': '10 to 16', 'from': 'Foster', 'to': 'Resi', 'n': 0, 'id': 100},
    #                {'age_bracket': '10 to 16', 'from': 'Foster', 'to': 'Other', 'n': 10, 'id': 101}]
    #
    session.calculate_model(model_params, [])

    return dict(
        base_pop_graph=session.model.base_pop_graph,
        adj_pop_graph=session.model.adj_pop_graph,
    )


@app.route('/costs')
def caclulate_costs():
    if session.model is None:
        return dict(error='No model calculated yet')

    base_costs = {'Foster': {'friend_relative': 10, 'in_house': 20, 'IFA': 30, },
                  'Resi': {'in_house1': 40, 'external': 60},
                  'Supported': {'Sup': 40, },
                  'Other': {'secure_home': 150, 'with_family': 30, 'any_other': 40}}

    cost_dict = {'base': base_costs}  # , 'adjusted': adjusted_costs}

    proportions = {'Foster': {'friend_relative': 0.5, 'in_house': 0.2, 'IFA': 0.3, },
                   'Resi': {'in_house1': 0.4, 'external': 0.6},
                   'Supported': {'Sup': 1, },
                   'Other': {'secure_home': 0.7, 'with_family': 0.1, 'any_other': 0.2}}

    cost_params = {'cost_dict': cost_dict,
                   'proportions': proportions,
                   'inflation': 0.2,
                   'step_size': '4m'
                   }

    session.calculate_costs(cost_params)

    return dict(
        base_cost_graph=session.model.base_cost_graph,
        adj_cost_graph=session.model.adj_cost_graph,
    )


@app.route('/samplefiles')
def sample_files():
    files = ezfiles()
    files = [
        {
            'description': f['description'],
            'year': f['year'],
            'path': f['path'],
            'name': f['name'],
            'size': f['size'],
            'lastModified': f['last_modified'],
            'type': f['type'],
            'data': b64encode(f['fileText']).decode('ascii'),
        } for f in files
    ]
    return dict(files=files)


if __name__ == "__main__":
    app.run(debug=True)
