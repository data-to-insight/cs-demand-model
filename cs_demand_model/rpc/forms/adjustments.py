from cs_demand_model.rpc.components import Fragment, Paragraph, TextField


def _add_field(from_type, to_type, age_bracket):
    return TextField(
        title=f"{from_type.label} -> {to_type.label} ({age_bracket.label})",
        id=f"adjustments|{from_type.name}|{to_type.name}|{age_bracket.name}".lower(),
    )


class AdjustmentsForm(Fragment):
    def __init__(self, state: "DemandModellingState"):
        AB = state.config.AgeBrackets
        PC = state.config.PlacementCategories
        super().__init__(
            Paragraph(
                'Add hypothetical monthly transfers between two placement types to compare this "adjusted" '
                'scenario with the "base" scenario',
                strong=True,
            ),
            Paragraph(
                "Add the number of children you expect to see per month. To increase the calculated rates, use "
                "positive numbers, to decrease the calculated rates, use negative numbers."
            ),
            _add_field(PC.FOSTERING, PC.RESIDENTIAL, AB.FIVE_TO_TEN),
            _add_field(PC.FOSTERING, PC.RESIDENTIAL, AB.TEN_TO_SIXTEEN),
            _add_field(PC.FOSTERING, PC.RESIDENTIAL, AB.SIXTEEN_TO_EIGHTEEN),
            _add_field(PC.FOSTERING, PC.SUPPORTED, AB.SIXTEEN_TO_EIGHTEEN),
            _add_field(PC.RESIDENTIAL, PC.FOSTERING, AB.FIVE_TO_TEN),
            _add_field(PC.RESIDENTIAL, PC.FOSTERING, AB.TEN_TO_SIXTEEN),
            _add_field(PC.RESIDENTIAL, PC.FOSTERING, AB.SIXTEEN_TO_EIGHTEEN),
            _add_field(PC.RESIDENTIAL, PC.SUPPORTED, AB.SIXTEEN_TO_EIGHTEEN),
            _add_field(PC.SUPPORTED, PC.FOSTERING, AB.SIXTEEN_TO_EIGHTEEN),
            _add_field(PC.SUPPORTED, PC.RESIDENTIAL, AB.SIXTEEN_TO_EIGHTEEN),
            padded=True,
        )
