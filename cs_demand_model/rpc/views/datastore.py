from cs_demand_model.rpc.components import (
    BoxPage,
    Button,
    ButtonBar,
    FileUpload,
    Paragraph,
)
from cs_demand_model.rpc.state import DemandModellingState
from cs_demand_model_samples import V1


class DataStoreView:
    def action(self, action, state: DemandModellingState, data):
        """
        This is called whenever an action is triggered for this view
        """
        if action == "use_sample_files":
            state.datastore = V1.datastore
        elif action == "upload_files":
            for id, f in data.items():
                state.add_file(id, f)
        elif action == "datastore_ready":
            if len(state.files) > 0:
                state.datastore_ready = True
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
            FileUpload(
                id="files",
                action="upload_files",
                title="Drop your SSDA903 files here or click to select",
            ),
            ButtonBar(
                Button(
                    "Next", action="datastore_ready", disabled=len(state.files) == 0
                ),
                Button(
                    "Use sample files", action="use_sample_files", variant="outlined"
                ),
            ),
            id="datastore_view",
        )
