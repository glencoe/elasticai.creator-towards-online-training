from elasticai.creator.vhdl.code_generation.code_abstractions import to_vhdl_binary_string
from elasticai.creator.file_generation.savable import Path
from elasticai.creator.file_generation.template import (
    InProjectTemplate,
    module_to_package,
)
from elasticai.creator.vhdl.design.ports import Port


class Skeleton:
    def __init__(
        self,
        x_num_values: int,
        y_num_values: int,
        network_name: str,
        port: Port,
        id: list[int] | int,
        skeleton_version: str
    ):
        self.name = "skeleton"
        self._network_name = network_name
        self._port = port
        self._x_num_values = str(x_num_values)
        self._y_num_values = str(y_num_values)
        if isinstance(id, int):
            id = [id]
        self._id = id
        if skeleton_version == "v1":
            self._template_file_name = "network_skeleton.tpl.vhd"
            if len(id) != 1:
                raise Exception(f"should give an id of 1 byte. Actual length is {len(id)}")
        elif skeleton_version == "v2":
            self._template_file_name = "network_skeleton_v2.tpl.vhd"
            if len(id) != 16:
                raise Exception(f"should give an id of 16 byte. Actual length is {len(id)}")
        else:
            raise Exception(f"Skeleton version {skeleton_version} does not exist")

    def save_to(self, destination: Path):
        template = InProjectTemplate(
            package=module_to_package(self.__module__),
            file_name=self._template_file_name,
            parameters=dict(
                name=self.name,
                network_name=self._network_name,
                data_width_in=str(self._port["x"].width),
                x_addr_width=str(self._port["x_address"].width),
                x_num_values=self._x_num_values,
                y_num_values=self._y_num_values,
                data_width_out=str(self._port["y"].width),
                y_addr_width=str(self._port["y_address"].width),
                id=", ".join(map(to_vhdl_binary_string, self._id))
            ),
        )
        file = destination.as_file(".vhd")
        file.write(template)

class LSTMSkeleton:
    def __init__(self, network_name: str):
        self.name = "skeleton"
        self._network_name = network_name

    def save_to(self, destination: Path):
        template = InProjectTemplate(
            package=module_to_package(self.__module__),
            file_name="lstm_network_skeleton.tpl.vhd",
            parameters=dict(name=self.name, network_name=self._network_name),
        )
        file = destination.as_file(".vhd")
        file.write(template)
