from cs_demand_model.rpc.components import Fragment, Paragraph, TextField


class CostProportionsForm(Fragment):
    def __init__(self, state: "DemandModellingState"):
        costs = [
            TextField(f"cost_proportions_{c.id}", c.label) for c in state.config.costs
        ]
        super().__init__(
            Paragraph(
                "Adjust the proportion of children per category to generate an adjusted cost forecast. "
                'e.g. Enter "0.5" under "Fostering (friend/relative)" for a scenario where half the '
                "children in fostering are with friends/relatives, "
                'then click "Calculate Now" below.',
                strong=True,
            ),
            *costs,
            padded=True,
        )
