from creator.file_generation.savable import Path
from creator.file_generation.template import InProjectTemplate, module_to_package
from creator.nn.fixed_point.number_converter import NumberConverter, FXPParams
from elasticai.creator.vhdl.simulated_layer import Testbench


class Conv1dTestbench(Testbench):
    def __init__(self, name: str, fxp_params: FXPParams):
        self._converter = NumberConverter(fxp_params)
        self._name = name

    def save_to(self, destination: Path):
        template = InProjectTemplate(
            package=module_to_package(self.__module__),
            file_name="testbench.tpl.vhd",
            parameters={"name": self.name}
        )
        destination.as_file(".vhd").write(template)

    @property
    def name(self) -> str:
        return self._name

    def prepare_inputs(self, *inputs) -> list[dict]:
        batches = inputs[0]
        prepared_inputs = []
        for batch in batches:
            prepared_inputs.append({})
            for channel_id, channel in enumerate(batch):
                for time_step_id, time_step_val in enumerate(channel):
                    prepared_inputs[-1][f"x_{channel_id}_{time_step_id}"] = \
                        self._converter.rational_to_bits(time_step_val)

        return prepared_inputs

    def set_inputs(self, *inputs) -> None:
        pass

    def parse_reported_content(self, content: list[str]) -> list[list[float]]:
        out_channel_content = content[0]
        out_channel_content = out_channel_content.split(",")
        out_channel_content = [self._converter.bits_to_rational(y) for y in out_channel_content]
        return [out_channel_content]