
import logging

class SimulationParameters():

    # def __init__(self, project):
    #     self.project = project
    #     read_parameters()

    def read_parameters(self, filepath):
        """ Read the simulation parameters from the MCERD input file """
    
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
            with open(filepath) as file:
                lines = file.readlines()
            for line in lines:
                line.lstrip()
                for key, value in params.items():
                    if line.startswith(key):
                        val = line.partition(':')[2].lstrip().rstrip().split()
                        if len(val) < 3:
                            params[key] = val[0]
                        else:
                            params[key] = (val[0], val[1])
    
            for key, value in params.items():
                print(value)

        except IOError:
            print("The file " + filepath + " doesn't exist. ")
            # msg = 'The file {0} doesn'
            # logging.getLogger('project').error('')

        self.__read_target_description_file(params["Target description file:"])
        # __read_detector_description_file(params["Detector description file:"])
        # __read_recoiling_material_distribution(params["Recoiling material distribution:"])


    def __read_target_description_file(self, filepath):
        try:
            with open(filepath) as file:
                lines = file.readlines()
            numberOfLines = len(lines)
            tmp = []
            start = 0
            for i in range(0,numberOfLines):
                # Currently we except that only one empty line separates the layers in the file
                if lines[i] == "\n":
                    block = list(map(str.rstrip, lines[start:i])) # map(str.rstrip, lines[start:i])
                    tmp.append(block)
                    i += 1
                    start = i
            tmp.append(lines[start:numberOfLines])
            print(tmp)

        except IOError:
            print("The file " + filepath + " doesn't exist. ")
            # msg = 'The file {0} doesn'
            # logging.getLogger('project').error('')
        return

    #def __read_detector_description_file(self, filepath):
    #    return

    #def __read_recoiling_material_distribution(self, filepath):
    #    return

SimulationParameters().read_parameters("/home/atsejaas/Downloads/Monisiro/source/Examples/35Cl-85-LiMnO_Li")
