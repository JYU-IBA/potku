

class SimulationParameters():




    def save_parameters(self, filepath=None):
        #example filepath
        filepath = "C:\\MyTemp\\testikirjoitus\\"
        foilsname = "ilmaisinkerrokset.foils"

        foil_elements = ["12.011 C", "14.00 N", "28.09 Si"]
        foil_layers = [
            {"thickness": "0.1 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL", "density": "0.1 g/cm3", "amount": ["0 1.0"]},
            {"thickness": "13.3 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL", "density": "2.25 g/cm3", "amount": ["0 1.0"]},
            {"thickness": "44.4 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL", "density": "2.25 g/cm3", "amount": ["0 1.0"]},
            {"thickness": "1.0 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL", "density": "3.44 g/cm3", "amount": ["1 0.57", "2 0.43"]}
        ]

        #form the list that will be written to the file
        foil_list = []
        for elem in foil_elements:
            foil_list.append(elem)
            foil_list.append("\n")

        foil_list.append("\n")

        for item in foil_layers:
            thickness = item.get("thickness")
            spfb = item.get("stopping power for beam")
            spfr = item.get("stopping power for recoil")
            density = item.get("density")
            amount = item.get("amount")

            foil_list.append(thickness + "\n")
            foil_list.append(spfb + "\n")
            foil_list.append(spfr + "\n")
            foil_list.append(density + "\n")

            for measure in amount:
                foil_list.append(measure + "\n")

            foil_list.append("\n")

        #remove the unnecessary line break at the end of the list (now it matches the example file structure)
        foil_list.pop()

        # call for saving the detector foils
        with open(filepath + foilsname, "w") as file2:
            for item in foil_list:
                file2.write(item)


        detector = {"Detector type:": "TOF", "Detector angle:": "41.12", "Virtual detector size:": "2.0 5.0", "Timing detector numbers:": "1 2", "Description file for the detector foils:": foilsname}
        foils = [
            {"Foil type:": "circular", "Foil diameter:": "7.0", "Foil distance:": "256.0"},
            {"Foil type:": "circular", "Foil diameter:": "9.0", "Foil distance:": "319.0"},
            {"Foil type:": "circular", "Foil diameter:": "18.0", "Foil distance:": "924.0"},
            {"Foil type:": "rectangular", "Foil size:": "14.0 14.0", "Foil distance:": "957.0"}
        ]

        separator1 = "=========="
        separator2 = "----------"

        #save the detector parameters
        with open(filepath + "ilmaisin.JyU", "w") as file1:
            file1.write("Ilmaisimen tietoja..")

        #call for saving target details
        with open(filepath + "kohtio.nayte", "w") as file3:
            file3.write("Tietoja näytteestä..")

        #call for saving recoiling distribution
        with open(filepath + "rekyyli.nayte_alkuaine", "w") as file4:
            file4.write("Tietoja jakaumasta..")

        # call for saving the mcerd command
        with open(filepath + "sade-nayte_alkuaine", "w") as file5:
            file5.write("Komentotiedosto..")


SimulationParameters().save_parameters()