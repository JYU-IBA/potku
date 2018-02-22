# coding=utf-8
'''
Created on 5.4.2013
Updated on 23.5.2013

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) Jarkko Aalto, Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen and 
Miika Raunio

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').

DepthFiles.py creates the files necessary for generating depth files.
Also handles several tasks necessary for operating with depth files.
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import os
import platform
import re
import subprocess

class DepthFiles(object):
    '''DepthFiles handles calling the external programs to create depth files.
    '''
    def __init__(self, filepaths, outputpath):
        '''Inits DepthFiles
        
        Args:
            filepaths: Full paths of cutfiles to be used.
            outputpath: Full path of where depth files are to be created.
        '''
        filepaths_str = ' '.join(filepaths)
        self.bin_dir = '%s%s%s' % ('external', os.sep, 'Potku-bin')
        self.command_win = 'cd ' + self.bin_dir + ' && tof_list.exe ' \
            + filepaths_str + ' | erd_depth.exe ' + outputpath + ' tof.in'
        self.command_unix = 'cd ' + self.bin_dir + ' && ./tof_list ' \
            + filepaths_str + ' | ./erd_depth ' + outputpath + ' tof.in'
   
   
    def create_depth_files(self):
        '''Generate the files necessary for drawing the depth profile
        '''
        used_os = platform.system()
        if used_os == 'Windows':
            subprocess.call(self.command_win, shell=True)
        elif used_os == 'Linux':
            subprocess.call(self.command_unix, shell=True)
        elif used_os == 'Darwin':
            subprocess.call(self.command_unix, shell=True)
        else:
            print('It appears we do no support your OS.')
            
        
def extract_from_depth_files(files, elements, x_column, y_column):
    '''Extracts two columns from each depth file.
    
    Args:
        files: List of depth files
        elements: List of used elements
        x_column: Integer of which column is to be extracted for 
        graph's x-axis
        y_column: Integer of which column is to be extracted for 
        graph's y-axis
        
    Return:
        List of lists. Each of these lists contains the element 
        of the file and two lists for graph plotting.
    '''
    read_files = []
    elements_str = []
    for element in elements:
        elements_str.append(str(element))
        
    for file in files:
        file_element = file.split('.')[-1]
        if file_element not in elements_str:
            for element in elements_str:
                if re.match('^[0-9]+' + file_element, element):
                    file_element = element
        axe1 = []
        axe2 = []
        for line in open(file):
            columns = re.split(' +', line.strip())
            axe1.append(float(columns[x_column]))
            axe2.append(float(columns[y_column]) * 100)
        read_files.append([file_element, axe1, axe2])
    return read_files
        

def create_relational_depth_files(read_files):
    '''Creates a version of the loaded depth files, which contain 
    the value of the y-axis in relation to the .total file's 
    y-axis, instead of their absolute values
    
    Args:
        read_files: The original files with absolute values.
        
    Return:
        A list filled with relational values in accordance to the 
        .total file.
    '''
    rel_files = []
    total_file_axe = []
    for file in read_files:
        file_element, axe1, axe2 = file
        if file_element == 'total':
            total_file_axe = axe2
            break
    for file in read_files:
        file_element, axe1, axe2 = file
        rel_axe = []
        i = 0
        while i < len(axe2) and i < len(total_file_axe):
            division = total_file_axe[i]
            if division != 0:
                rel_val = (axe2[i] / total_file_axe[i]) * 100
            else:
                rel_val = 0
            rel_axe.append(rel_val)
            i += 1
        rel_files.append([file_element, axe1, rel_axe])
    return rel_files


def merge_files_in_range(fil_a, fil_b, lim_a, lim_b):
    '''Merges two lists that contain n amount of [str,[x],[y]] items.
    When within range [lim_a, lim_b] values from fil_b are used,
    otherwise values from fil_a.
    
    Args:
        fil_a: First file to be merged.
        fil_b: Second file to be merged.
        lim_a: The lower limit.
        lim_b: The higher limit.
    Return:
        A merged file.
    '''
    i = 0
    fil_c = []
    while i < len(fil_a):
        item = fil_a[i]
        new_item = [item[0], item[1], []]
        j = 0
        while j < len(item[1]):
            if item[1][j] >= lim_a and item[1][j] <= lim_b:
                new_item[2].append(fil_b[i][2][j])
            else:
                new_item[2].append(fil_a[i][2][j])
            j += 1
        i += 1
        fil_c.append(new_item)
    return fil_c


def integrate_lists(lists, lim_a, lim_b):
    '''Calculates and returns the relative amounts of values within lists.
    
    Args:
        lists: List of lists containing float values, the first list 
        is the one the rest are compared to.
        lim_a: The lower limit.
        lim_b: The higher limit.
    
    Return:
        List of lists filled with percentages.
    '''
    total_sum = float
    sums = []
    percentages = []
    # Extract the sum of data point within the [lim_a,lim_b]-range
    for lst in lists:
        i = 1
        p = []
        x = lst[1]
        y = lst[2]
        while True:  # TODO: for katso listanlukuolio
            curr = x[i]
            prev_val = y[i - 1]
            curr_val = y[i]
            if curr > lim_b:
                value = (prev_val + curr_val) / 2
                p.append(value)
                break
            elif curr < lim_a:
                pass
            elif curr >= lim_a and curr <= lim_b:
                value = (prev_val + curr_val) / 2
                p.append(value)
            i += 1
            if i == len(x):
                break
        sums.append(sum(p))
    # Calculate the relative sums
    has_total = False
    for element_sum in sums:
        if not has_total:
            total_sum = element_sum
            percentage = 100.0
            has_total = True
        else:
            if abs(total_sum) < 0.001:
                percentage = 0
            else:
                percentage = (element_sum / total_sum) * 100
        percentages.append(percentage)
    return percentages


def get_depth_files(elements, dir_cuts):
    '''Returns a list of depth files in a directory
    
    Args:
        elements: List of Element objects that should have a 
        corresponding depth file.
        dir_cuts: Directory of the cut files.
    Returns:
        A list of depth files which matched the elements.
    '''
    depth_files = []
    depth_files.append('depth.total')
    strip_elements = []
    for element in elements:
        strip_element = re.sub("\d+", "", str(element))
        strip_elements.append(strip_element)
    files = os.listdir(dir_cuts)
    for file in files:
        file_element = file.split('.')[-1]
        if file_element in strip_elements:
            depth_files.append(file)
    return depth_files

