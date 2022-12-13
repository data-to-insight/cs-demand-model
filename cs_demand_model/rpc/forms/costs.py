from cs_demand_model.rpc.components import Fragment, Paragraph, TextField


class CostsForm(Fragment):
    def __init__(self, state: "DemandModellingState"):
        costs = [
            TextField(f"costs_{c.id}", c.label, start_icon="currency_pound")
            for c in state.config.costs
        ]
        super().__init__(
            Paragraph(
                "To display a cost forecast, enter the average weekly costs for each placement type, "
                'then click "Calculate Now" below.',
                strong=True,
            ),
            *costs,
            padded=True,
        )
