
import logging

class SimulationParameters():

#     def __init__(self, project, file_path):
#         self.project = project
#         self.read_parameters(file_path)

    def __init__(self, file_path):
        self.foil_elements = []
        self.foil_layers = []
        self.read_parameters(file_path)

    def read_parameters(self, file_path):
        """ Read the simulation parameters from the MCERD input file
        
        Args:
            file_path: An absolute file path to MCERD input file
        """
    
        params = {
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
        }
        try:
            with open(file_path) as file:
                lines = file.readlines()
            for line in lines:
                line.lstrip()
                for key, value in params.items():
                    if line.startswith(key):
                        val = line.partition(':')[2].strip().split()
                        if len(val) < 3:
                            params[key] = val[0]
                        else:
                            params[key] = (val[0], val[1])

        except IOError:
            # TODO: Print to the project log 
            print("The file " + file_path + " doesn't exist. ")
            # msg = 'The file {0} doesn'
            # logging.getLogger('project').error('')

        self.__read_target_description_file(params["Target description file:"])
        #self.__read_detector_description_file(params["Detector description file:"])
        # __read_recoiling_material_distribution(params["Recoiling material distribution:"])

    def __read_target_description_file(self, file_path):
        """ Reads MCERD target description file.
        
        Args:
            file_path: An absolute file path to the MCERD target description file
        """
        try:
            with open(file_path) as file:
                # First we read all elements to "foil_elements"
                line = file.readline()
                while line != "\n":
                    self.foil_elements.append(line.strip())
                    line = file.readline()
                
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
                    self.foil_layers.append(tmp)

        except IOError:
            # TODO: Print to the project log 
            print("The file " + file_path + " doesn't exist. ")
            # msg = 'The file {0} doesn'
            # logging.getLogger('project').error('')
        return

    def __read_detector_description_file(self, file_path):
        detector_params = {
            "Detector type:": None,
            "Detector angle:": None,
            "Virtual detector size:": None,
            "Timing detector numbers:": None,
            "Description file for the detector foils:": None
        }
        layers = [
            {"Foil type: circular": None, "Foil diameter:": None, "Foil distance:": None}
        ]

        try:
            with open(file_path) as file:
                lines = file.readlines()
                for line in lines:
                    line.lstrip()
                    # here parse the line and put into detector_params accordingly
        except IOError as e:
            print(e)
        return

    #def __read_recoiling_material_distribution(self, file_path):
    #    return

# For test purposes only
SimulationParameters("/home/severij/Downloads/source/Examples/35Cl-85-LiMnO_Li")
