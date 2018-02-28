
import os, logging

class SimulationParameters():

#     def __init__(self, project, file_path):
#         self.project = project
#         self.read_parameters(file_path)

    def __init__(self, file_path):
        self.simulation = {}
        self.target = {}
        self.detector = {}
        self.recoil = []
        self.read_parameters(file_path)
        print(self.simulation)
        print(self.target)
        print(self.detector)
        print(self.recoil)

    def read_parameters(self, file_path):
        """ Read the simulation parameters from the MCERD input file
        
        Args:
            file_path: An absolute file path to MCERD input file
        """
    
        self.simulation.update({
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
                lines = file.readlines()
            for line in lines:
                for key in self.simulation:
                    if line.startswith(key):
                        val = line.partition(':')[2].strip().split()
                        if len(val) < 3:
                            self.simulation[key] = val[0]
                        else:
                            self.simulation[key] = (val[0], val[1])

        except IOError:
            # TODO: Print to the project log 
            print("The file " + file_path + " doesn't exist. ")
            # msg = 'The file {0} doesn'
            # logging.getLogger('project').error('')

        self.__read_layers(self.simulation["Target description file:"])
        self.__read_detector_file(self.simulation["Detector description file:"])
        self.__read_recoiling_material_distribution(self.simulation["Recoiling material distribution:"])

    def __read_layers(self, file_path):
        """
        Read MCERD target description file or a description file for detector foils.
        Both files should have similar format.
        
        Args:
            file_path: An absolute file path. Either target description file or
            a description file for detector foils.
        """
        try:
            with open(file_path) as file:
                elements = []
                layers = []
                line = file.readline()

                while line != "\n":
                    elements.append(line.strip())
                    line = file.readline()

                # Currently it's assumed that there's exactly one empty line here
                
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
                
                try:
                    if os.path.splitext(file_path)[1] == ".target":
                        self.target["elements"] = elements
                        self.target["layers"] = layers
                    elif os.path.splitext(file_path)[1] == ".foils":
                        self.detector["foils"]["elements"] = elements
                        self.detector["foils"]["layers"] = layers
                    else:
                        raise ValueError("File extension should be either "
                                         "'.target' or '.foils'")
                except:
                    # TODO: Print to the project log
                    print("jee")

        except IOError:
            # TODO: Print to the project log 
            print("The file " + file_path + " doesn't exist. ")
            # msg = 'The file {0} doesn'
            # logging.getLogger('project').error('')
        return

    def __read_detector_file(self, file_path):
        self.detector.update({
            "Detector type:": None,
            "Detector angle:": None,
            "Virtual detector size:": None,
            "Timing detector numbers:": None,
            "Description file for the detector foils:": None
        })
        foils = ["Foil type:", "Foil diameter:", "Foil distance:"]

        try:
            with open(file_path) as file:
                line = file.readline()
                while line != "":
                    for key in self.detector:
                        if line.startswith(key):
                            val = line.partition(':')[2].strip()
                            self.detector[key] = val
                            break
                    if not (None in self.detector.values()):
                        break
                    line = file.readline()

                while line != "":
                    for key in foils:
                        if not line.startswith(key):
                            line = file.readline()
                            continue
                    break

                self.detector["foils"] = {}
                dimensions = []

                while line != "":
                    tmp = {}
                    for i in range(0,3):
                        for key in foils:
                            if line.startswith(key):
                                val = line.partition(':')[2].strip()
                                tmp[key] = val
                                break
                        line = file.readline()
                    dimensions.append(tmp)
                    while line != "":
                        for key in foils:
                            if not line.startswith(key):
                                line = file.readline()
                                continue
                        break
                self.__read_layers(self.detector["Description file for the detector foils:"])
                self.detector["foils"]["dimensions"] = dimensions

        except IOError as e:
            print(e)


    def __read_recoiling_material_distribution(self, file_path):
        try:
            with open(file_path) as file:
                lines = file.readlines()
            for line in lines:
                self.recoil.append(line.strip().split())

        except IOError:
            # TODO: Print to the project log 
            print("The file " + file_path + " doesn't exist. ")
            # msg = 'The file {0} doesn'
            # logging.getLogger('project').error('')

# For test purposes only
SimulationParameters("/home/severij/Downloads/source/Examples/35Cl-85-LiMnO_Li")
