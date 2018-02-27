
class SimulationParameters:



    def save_foil_params(self, foilsname, filepath):
        foil_elements = ["12.011 C", "14.00 N", "28.09 Si"]
        foil_layers = [
            {"thickness": "0.1 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL",
             "density": "0.1 g/cm3", "amount": ["0 1.0"]},
            {"thickness": "13.3 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL",
             "density": "2.25 g/cm3", "amount": ["0 1.0"]},
            {"thickness": "44.4 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL",
             "density": "2.25 g/cm3", "amount": ["0 1.0"]},
            {"thickness": "1.0 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL",
             "density": "3.44 g/cm3", "amount": ["1 0.57", "2 0.43"]}
        ]

        # form the list that will be written to the file
        foil_list = []
        for elem in foil_elements:
            foil_list.append(elem)
            foil_list.append("\n")

        foil_list.append("\n")

        for layer in foil_layers:
            thickness = layer.get("thickness")
            spfb = layer.get("stopping power for beam")
            spfr = layer.get("stopping power for recoil")
            density = layer.get("density")
            amount = layer.get("amount")

            foil_list.append(thickness + "\n")
            foil_list.append(spfb + "\n")
            foil_list.append(spfr + "\n")
            foil_list.append(density + "\n")

            for measure in amount:
                foil_list.append(measure + "\n")

            foil_list.append("\n")

        # remove the unnecessary line break at the end of the list (now it matches the example file structure)
        foil_list.pop()

        # call for saving the detector foils
        with open(filepath + foilsname, "w") as file2:
            for item in foil_list:
                file2.write(item)

    def save_detector_params(self, detectorname, foilsname, filepath):
        detector = {"Detector type:": "TOF", "Detector angle:": "41.12", "Virtual detector size:": "2.0 5.0",
                    "Timing detector numbers:": "1 2", "Description file for the detector foils:": foilsname}
        foils = [
            {"Foil type:": "circular", "Foil diameter:": "7.0", "Foil distance:": "256.0"},
            {"Foil type:": "circular", "Foil diameter:": "9.0", "Foil distance:": "319.0"},
            {"Foil type:": "circular", "Foil diameter:": "18.0", "Foil distance:": "942.0"},
            {"Foil type:": "rectangular", "Foil size:": "14.0 14.0", "Foil distance:": "957.0"}
        ]

        separator1 = "=========="
        separator2 = "----------"

        detector_list = []
        for key, value in detector.items():
            detector_list.append(key + " " + value + "\n")

        detector_list.append(separator1 + "\n")

        for foil in foils:
            for key, value in foil.items():
                detector_list.append(key + " " + value + "\n")
            detector_list.append(separator2 + "\n")

        # remove the unnecessary line break and separator at the end of the list
        # (now it matches the example file structure)
        detector_list.pop()

        # save the detector parameters
        with open(filepath + detectorname, "w") as file1:
            for item in detector_list:
                file1.write(item)

    def save_target_params(self, targetname, filepath):
        target_elements = ["6.94 Li", "16.00 O", "28.09 Si", "54.94 Mn"]
        target_layers = [
            {"thickness": "0.01 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL",
             "density": "0.000001 g/cm3", "amount": ["0 1.0"]},
            {"thickness": "90 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL",
             "density": "4.0 g/cm3", "amount": ["0 0.048", "1 0.649", "3 0.303"]},
            {"thickness": "1000 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL",
             "density": "2.32 g/cm3", "amount": ["2 1.0"]}
        ]

        # form the list that will be written to the file
        target_list = []
        for elem in target_elements:
            target_list.append(elem)
            target_list.append("\n")

        target_list.append("\n")

        for layer in target_layers:
            thickness = layer.get("thickness")
            spfb = layer.get("stopping power for beam")
            spfr = layer.get("stopping power for recoil")
            density = layer.get("density")
            amount = layer.get("amount")

            target_list.append(thickness + "\n")
            target_list.append(spfb + "\n")
            target_list.append(spfr + "\n")
            target_list.append(density + "\n")

            for measure in amount:
                target_list.append(measure + "\n")

            target_list.append("\n")

        # remove the unnecessary line break at the end of the list (now it matches the example file structure)
        target_list.pop()
        # call for saving target details
        with open(filepath + targetname, "w") as file3:
            for item in target_list:
                file3.write(item)

    def save_recoil_params(self, recoilname, filepath):
        recoil_coordinates = [["0.00", "0.070"], ["95.00", "0.070"], ["95.01", "0.00001"], ["110.00", "0.00001"],
                              ["110.01", "0.00"], ["110.02", "0.00"]]
        recoil_list = []

        for pair in recoil_coordinates:
            x = pair[0]
            y = pair[1]
            recoil_list.append(x + " " + y + "\n")

        # call for saving recoiling distribution
        with open(filepath + recoilname, "w") as file4:
            for item in recoil_list:
                file4.write(item)

    def save_command_params(self, commandname, targetname, detectorname, recoilname, filepath):
        header1 = "******************* Type of the simulation *******************************"
        header2 = "*************** General physical parameters for the simulation ***********"
        header3 = "********** Physical parameters conserning specific simulation type *********"
        subheader = "----------------------- ERD -simulation ------------------------------------"
        header4 = "******************* Parameters with physical significance ******************"
        header5 = "******************* Nonphysical parameters for simulation ***************"

        arguments1 = {"Type of simulation:": "ERD"}
        arguments2 = {"Beam ion": "35Cl", "Beam energy": "8.515 MeV"}
        arguments3 = {"Target description file:": targetname, "Detector description file:": detectorname,
                      "Recoiling atom:": "7Li", "Recoiling material distribution:": recoilname,
                      "Target angle:": "20.6 deg", "Beam spot size:": "0.5 3.0 nm"}
        arguments4 = {"Minimum angle of scattering:": "0.05 deg", "Minimum main scattering angle:": "20 deg",
                      "Minimum energy of ions:": "1.5 MeV", "Average number of recoils per primary ion:": "10",
                      "Recoil angle width (wide or narrow):": "narrow",
                      "Presimulation * result file:": "Cl-10-R2_O.pre", "Number of real ions per each scaling ion:": "5"
                      }
        arguments5 = {"Number of ions:": "1000000", "Number of ions in the presimulation:": "100000",
                      "Seed number of the random number generator:": "101"}

        argument_list = []
        argument_list.append(header1 + "\n")
        arg_key, arg_value = list(arguments1.items())[0]
        argument_list.append(arg_key + " " + arg_value + "\n")

        argument_list.append(header2 + "\n")

        for key, value in arguments2.items():
            argument_list.append(key + " " + value + "\n")

        argument_list.append(header3 + "\n")
        argument_list.append(subheader + "\n")

        for key, value in arguments3.items():
            argument_list.append(key + " " + value + "\n")

        argument_list.append(header4 + "\n")

        for key, value in arguments4.items():
            argument_list.append(key + " " + value + "\n")

        argument_list.append(header5 + "\n")

        for key, value in arguments5.items():
            argument_list.append(key + " " + value + "\n")

        # call for saving the mcerd command
        with open(filepath + commandname, "w") as file5:
            for item in argument_list:
                file5.write(item)

    def save_parameters(self, filepath=None):
        # example filepath
        filepath = "C:\\MyTemp\\testikirjoitus\\"
        foilsname = "ilmaisinkerrokset.foils"
        detectorname = "ilmaisin.JyU"
        targetname = "kohtio.nayte"
        recoilname = "rekyyli.nayte_alkuaine"
        commandname = "sade-nayte_alkuaine"

        self.save_foil_params(foilsname, filepath)

        self.save_detector_params(detectorname, foilsname, filepath)

        self.save_target_params(targetname, filepath)

        self.save_recoil_params(recoilname, filepath)

        self.save_command_params(commandname, targetname, detectorname, recoilname, filepath)

SimulationParameters().save_parameters()
