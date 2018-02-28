# TODO: Add licence information

import os, logging

class SimulationParameters():

    def __init__(self, file_path):
        self.read_parameters(file_path)

    def read_parameters(self, file_path):
        """ Read the MCERD command file
        
        Args:
            file_path: An absolute file path to MCERD command file
        """

        # Initialize few simulation parameters. The key values are used later on
        # for checking if a line starts with that specific key. These are
        # the same as in MCERDs read_input.h header file.
        self.simulation = {
            "Type of simulation:": None,
            "Beam ion:": None,
            "Beam energy:": None,
            "Target description file:": None,
            "Detector description file:": None,
            "Recoiling atom:": None,
            "Recoiling material distribution:": None,
            "Target angle:": None,
            "Beam spot size:": None,
            "Minimum angle of scattering:": None,
            "Minimum energy of ions:": None,
            "Number of ions:": None,
            "Number of ions in the presimulation:": None,
            "Average number of recoils per primary ion:": None,
            "Seed number of the random number generator:": None,
            "Recoil angle width (wide or narrow):": None,
            "Minimum main scattering angle:": None,
            "Beam divergence:": None,
            "Beam profile:": None,
            "Surface topography file:": None,
            "Side length of the surface topography image:": None,
            "Number of real ions per each scaling ion:": None
        })

        try:
            with open(file_path) as file:
                lines = file.readlines() # Read all lines of the file to list
            for line in lines:

                # Check if the current line starts with any of the keys in
                # simulation dictionary. If not, the line is just skipped.
                for key in self.simulation:
                    if line.startswith(key):
                        val = line.partition(':')[2].strip().split()

                        # Some of the parameters in command file have more than
                        # one values. Also, some of them have units, e.g.
                        # "10 deg", so we just want to ignore the units.
                        if len(val) < 3:
                            self.simulation[key] = val[0]
                        else:
                            self.simulation[key] = (val[0], val[1])

            # In the command file there are several other file paths specified.
            # There are the target and detector description files and
            # recoiling material distribution file.
            self.read_layers(self.simulation["Target description file:"])
            self.read_detector_file(self.simulation["Detector description file:"])
            self.read_recoiling_material_distribution(self.simulation["Recoiling material distribution:"])

        # If we cannot read the command file, we except an IOError
        except IOError:
            # TODO: Print to the project log 
            print("Cannot read file " + file_path)
            # msg = 'The file {0} doesn'
            # logging.getLogger('project').error('')

    def read_layers(self, file_path):
        """
        Read MCERD target description file or a description file for detector
        foils. Both files should have similar format.
        
        Args:
            file_path: An absolute file path. Either target description file or
            a description file for detector foils.
        """
        try:
            with open(file_path) as file:
                elements = []
                layers = []
                line = file.readline()

                # The first few lines should specify the elements
                while line != "\n":
                    elements.append(line.strip())
                    line = file.readline()

                # Currently it's assumed that there's exactly one empty line
                # here. !!! TODO: It might be a good idea to change this

                # Read all the different layers one by one
                while line != "":
                    tmp = {} 
                    amount = []
                    tmp["thickness"] = file.readline().strip()
                    tmp["stopping power for beam"] = file.readline().strip()
                    tmp["stopping power for recoil"] = file.readline().strip()
                    tmp["density"] = file.readline().strip()
                    line = file.readline()
                    while line != "\n" and line != "":
                        amount.append(line.strip())
                        line = file.readline()
                    tmp["amount"] = amount
                    layers.append(tmp)

                # The file can be either target description file or
                # description file for detectors foils, so function should
                # check which one is it, so it can save the parameters
                # to right attributes.
                file_name = os.path.splitext(file_path)
                try:
                    if file_name[0] == "target" or file_name[1] == ".target":
                        self.simulation["target"] = {}
                        self.simulation["target"]["elements"] = elements
                        self.simulation["target"]["layers"] = layers
                    elif os.path.splitext(file_path)[1] == ".foils":
                        self.detector["foils"]["elements"] = elements
                        self.detector["foils"]["layers"] = layers
                    else:
                        # If the file is neither of these, the function should
                        # raise an error.
                        raise ValueError("File extension should be either "
                                         "'.target' or '.foils'")
                except:
                    # TODO: Print to the project log

        except IOError:
            # TODO: Print to the project log 
            print("The file " + file_path + " doesn't exist. ")

    def read_detector_file(self, file_path):
        """ Read MCERD detector description file.

        Args:
            An absolute file path to MCERD decector description file
        """

        # Initialize few detector parameters. These parameters should be
        # located in the beginning of the detector description file.
        self.simulation["detector"] = {
            "Detector type:": None,
            "Detector angle:": None,
            "Virtual detector size:": None,
            "Timing detector numbers:": None,
            "Description file for the detector foils:": None
        }

        # This list is not saved in detectors attributes. It is just used
        # later for checking line beginnings in a file.
        foils = ["Foil type:", "Foil diameter:", "Foil size:", "Foil distance:"]

        try:
            with open(file_path) as file:
                line = file.readline()
                while line != "":

                    # Here we check if the current line starts with any of the
                    # keys in the simulation["detector"] dictionary.
                    for key in self.simulation["detector"]:
                        if line.startswith(key):
                            val = line.partition(':')[2].strip()
                            self.simulation["detector"][key] = val
                            break

                    # Stop if we have all five first parameters in the
                    # dictionary
                    if not (None in self.simulation["detector"].values()):
                        break
                    line = file.readline()

                # Skip empty lines and lines that doesn't have any necessary
                # information.
                while line != "":
                    for key in foils:
                        if not line.startswith(key):
                            line = file.readline()
                            continue
                    break

                self.simulation["detector"]["foils"] = {}
                dimensions = []

                while line != "":

                    tmp = {}

                    # Here we except that the foil dimensions (foil type, foil
                    # diameter/foil size, foil distance) are in groups of three
                    # lines in the description file.
                    for i in range(0,3):
                        for key in foils:
                            if line.startswith(key):
                                val = line.partition(':')[2].strip()
                                tmp[key] = val
                                break
                        line = file.readline()
                    dimensions.append(tmp)

                    # Skip empty lines and lines that doesn't have any necessary
                    # information.
                    while line != "":
                        for key in foils:
                            if not line.startswith(key):
                                line = file.readline()
                                continue
                        break
                self.read_layers(self.detector["Description file for the detector foils:"])
                self.simulation["detector"]["foils"]["dimensions"] = dimensions

        except IOError as e:
            print(e)


    def read_recoiling_material_distribution(self, file_path):
        """ Read recoiling material distribution

        Args:
            file_path: An aboslute file path to recoiling material distribution
            file.
        """
        try:
            with open(file_path) as file:
                lines = file.readlines()
                self.simulation["recoil"] = []
                # We simply read the recoiling material distribution
                # coordinates to a list.
            for line in lines:
                self.simulation["recoil"].append(line.strip().split())

        except IOError:
            # TODO: Print to the project log 
            print("Cannot read file" + file_path)
            # msg = 'The file {0} doesn'
            # logging.getLogger('project').error('')


