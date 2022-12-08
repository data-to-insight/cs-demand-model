from cs_demand_model.rpc.components import BoxPage, Button, ButtonBar, Paragraph
from cs_demand_model.rpc.state import DemandModellingState
from cs_demand_model_samples import V1


class DataStoreView:
    def action(self, action, state: DemandModellingState, data):
        """
        This is called whenever an action is triggered for this view
        """
        if action == "use_sample_files":
            state.datastore = V1.datastore
        return state

    def render(self, state: DemandModellingState):
        return BoxPage(
            Paragraph(
                "This tool automatically forecasts demand for children’s services "
                "placements so that commissioners can conduct sufficiency analyses, "
                "secure appropriate budgets for services and demonstrate the business "
                "case for a new or changed service."
            ),
            Paragraph(
                "Load your local authority’s historic statutory return files on looked "
                "after children (SSDA903 files) to quickly see estimates of future "
                "demand for residential, fostering and supported accommodation "
                "placements."
            ),
            Paragraph(
                "Adjust population and cost parameters to model changes you are "
                "considering, such as the creation of in-house provision, or a "
                "step-down service."
            ),
            Paragraph(
                "Note: You do not need data sharing agreements to use this tool. "
                "Even though it opens in your web-browser, the tool runs offline, "
                "locally on your computer so that none of the data you enter leaves "
                "your device."
            ),
            Paragraph(
                "Drop your SSDA903 return files in below to begin generating forecasts!"
            ),
            ButtonBar(Button("Use sample files", action="use_sample_files")),
        )
