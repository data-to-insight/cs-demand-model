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
def calculate_costs():
    if session.model is None:
        return dict(error='No model calculated yet')

    costs = {
        'Fostering(friend / relative)': 100,
        'Fostering (in-house)': 111,
        'Fostering (IFA)': 1000,
        'Residential (in-house)': 20,
        'Residential (external)': 207,
        'Supported': 2077,
        'Secure home': 240,
        'Placed with family': 2440,
        'Other': 240
    }

    props = {
        'Fostering(friend / relative)': 0.5,
        'Fostering (in-house)': 0.5,
        'Fostering (IFA)': 0,
        'Residential (in-house)': 0.4,
        'Residential (external)': 0.6,
        'Supported': 1,
        'Secure home': 0.2,
        'Placed with family': 0.4,
        'Other': 0.4
    }

    session.calculate_costs(costs, props)

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
