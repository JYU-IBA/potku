

class SimulationParameters():

    def read_parameters(filepath):
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
            "Presimulation result file:": None,
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
            print('Could not read file ' + filepath)
