from cs_demand_model.rpc.components import DateSelect, Fragment, Paragraph, TextField


class ModelDatesForm(Fragment):
    def __init__(self):
        super().__init__(
            Paragraph(
                "Which period of the historical data should the model learn from?",
                strong=True,
            ),
            DateSelect("start_date", "Reference Start Date"),
            DateSelect("end_date", "Reference End Date"),
            Paragraph("What is the forecast period?"),
            DateSelect("prediction_start_date", "Forecast Start Date"),
            DateSelect("prediction_end_date", "Forecast End Date"),
            TextField(
                "step_size",
                "Step Size (in days)",
                input_props=dict(inputMode="numeric", pattern="[0-9]*"),
            ),
            padded=True,
        )
