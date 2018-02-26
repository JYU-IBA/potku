

class SimulationParameters():




    def save_parameters(self, filepath=None):
        #example filepath
        filepath = "C:\\MyTemp\\testikirjoitus\\"

        foil_elements = ["12.011 C", "14.00 N", "28.09 Si"]
        foil_layers = [
            {"thickness": "0.1 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL", "density": "0.1 g/cm3", "amount": ["0 1.0"]},
            {"thickness": "13.3 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL", "density": "2.25 g/cm3", "amount": ["0 1.0"]},
            {"thickness": "44.4 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL", "density": "2.25 g/cm3", "amount": ["0 1.0"]},
            {"thickness": "1.0 nm", "stopping power for beam": "ZBL", "stopping power for recoil": "ZBL", "density": "3.44 g/cm3", "amount": ["1 0.57", "2 0.43"]}
        ]

        #form the list that will be written to the file
        foils = []
        for elem in foil_elements:
            foils.append(elem)
            foils.append("\n")

        foils.append("\n")

        for item in foil_layers:
            thickness = item.get("thickness")
            spfb = item.get("stopping power for beam")
            spfr = item.get("stopping power for recoil")
            density = item.get("density")
            amount = item.get("amount")

            foils.append(thickness + "\n")
            foils.append(spfb + "\n")
            foils.append(spfr + "\n")
            foils.append(density + "\n")

            for measure in amount:
                foils.append(measure + "\n")

            foils.append("\n")

        #remove the unnecessary line break at the end of the list (now it matches the example file structure)
        foils.pop()
        # call for saving the detector foils
        with open(filepath + "ilmaisinkerrokset.foils", "w") as file2:
            for item in foils:
                file2.write(item)


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