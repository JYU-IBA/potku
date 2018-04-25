
import subprocess
import platform
import datetime
import json
import os

class ElementSimulation():

    __slots__ = "type", "element", "profile", "name", "description",\
                "modification_time"

    def __init__(self, type, element, profile, name="", description="",
                 modification_time=datetime.datetime.now()):
        """Initializes an ElementSimulation object.

        Args:
            type:              Type of the simulation (String, either
                               "recoiling" or "scattering").
            element:           An element (either recoiling or scattering) that will
                               be used in the simulation.
            profile:           A recoil atom distribution profile for the element.
            name:              Name of the particular element simulation.
            description:       A description given for the element simulation.
            modification_time: A modification time in ISO 8601 format, without
                               information about the timezone.
        """
        self.name = name
        self.description = description
        self.modification_time = modification_time
        self.type = type
        self.element = element
        self.profile = profile

        self.__command = os.path.join("external", "Potku-bin", "mcerd" +
            (".exe" if platform.system() == "Windows" else ""))
        self.__process = None

    @classmethod
    def from_file(cls, file_path):

        obj = json.load(open(file_path))

        name = obj["name"]
        description = obj["description"]

        # Convert string to datetime object. The string is assumed to be in
        # ISO 8601 format, without information about the timezone.
        # TODO: Add timezone.
        modification_time = datetime.datetime.strptime(obj["modification_time"],
                                                       "%Y-%m-%dT%H:%M:%S")

        type = obj["type"]
        element = obj["element"]
        profile = []  # TODO: Finish this.

        cls(type, element, profile, name, description, modification_time)

    def to_file(self, file_path):

        # Convert datetime object to string. Put the string in ISO 8601 format
        #  without information about the timezone. TODO: Add timezone
        obj = {
            "name": self.name,
            "description": self.description,
            "modification_time": datetime.datetime.now().isoformat(
                timespec="seconds"),
            "type": self.type,
            "element": self.element,
            "profile": []  # TODO: Finish this.
        }

        json.dump(obj, file_path)


    def start(self):
        """Start the simulation."""
        self.mcerd = MCERD(settings)

    def stop(self):
        """Stop the simulation."""
        del(self.mcerd)

    def pause(self):
        """Pause the simulation."""
        # TODO: Implement this sometime in the future.
        pass
