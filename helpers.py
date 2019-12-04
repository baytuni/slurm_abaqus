import os
import sys
import re
import shutil
import fnmatch
import subprocess
import time 
import socket

from constants import AbaqusConstants, LicenseConstants


def find_the_line(pattern_1, pattern_2, filename):
    for line in open(filename, 'r'):
        if re.search(pattern_1, line, re.IGNORECASE):
            if re.search(pattern_2, line, re.IGNORECASE):
                yield line
    yield None 

def get_step_lines(input_file_name):
    reg_switch = False
    step_lines_collection = []
    step_lines = []

    for line in open(input_file_name, 'r'):
        if re.search('\*step', line, re.IGNORECASE):
            reg_switch = True
        elif re.search('\*end step', line, re.IGNORECASE):
            reg_switch = False
            step_lines.append(line)
            step_lines_collection.append(step_lines.copy())
            step_lines = []
        if reg_switch:
            step_lines.append(line)

    return step_lines_collection


'''
Generic function to delete, move, or copy all the files from a given 
directory based on matching pattern
'''
def wildcard_operations(sourcePath, pattern, 
                        operation='remove', targetPath=None):
    listOfFilesWithError = []
    parentDir, _, filenames = next(os.walk(sourcePath))
    for filename in fnmatch.filter(filenames, pattern):
        try:
            if operation == 'remove':
                os.remove(os.path.join(parentDir, filename))
            if operation == 'move' and targetPath:
                shutil.move(os.path.join(parentDir, filename), 
                            targetPath)
            if operation == 'copy' and targetPath:
                shutil.copy2(os.path.join(parentDir, filename), 
                            targetPath)
        except:
            print("Error while deleting file : ", 
                 os.path.join(parentDir, filename))
            listOfFilesWithError.append(os.path.join(parentDir, filename))
    return listOfFilesWithError

def create_scratch_and_move(input_file_name,job_folder_name):
    # If there is no folder in the scratch_dir, make one and copy
    #the input file
    scratch_job_folder = os.path.join(AbaqusConstants.SCRATCH_FOLDER,
                                      job_folder_name)
    if not os.path.isdir(scratch_job_folder):
        os.mkdir(scratch_job_folder)
        shutil.copy(input_file_name, scratch_job_folder)
        #Read additional files from the file and copy them to scratch
        include_file_lines = look_for_include_files(input_file_name)
        for folder_name, file_name in include_file_lines:
            scratch_include_path = os.path.join(scratch_job_folder,
                                                folder_name)
            include_file_path = os.path.join(folder_name, file_name)

            if not os.path.exists(scratch_include_path):
                os.makedirs(scratch_include_path)
            shutil.copy(include_file_path, scratch_include_path)


    
def merge_res_files(job_name):
    #Renaming all the res files to original filenames
    for ext in AbaqusConstants.FILE_EXTENSIONS:

        if not os.path.isfile(u'Res_' + job_name + ext):
            continue

        print("Merging {} files".format(ext))
        if ext in AbaqusConstants.OUTPUT_FILE_EXTENSIONS:
            with open(job_name + ext, 'a') as outfile:
                with open(u'Res_' + job_name + ext) as infile:
                    outfile.write(infile.read())
            os.remove(u'Res_' + job_name + ext)
        else:
            try:
                shutil.move(u'Res_' + job_name + ext, job_name + ext)         
            except:
                pass

def copy_dat_file(job_name, submit_dir):

    shutil.copy2(os.path.join(os.getcwd(), job_name + '.dat'), submit_dir)
    print("Job produced a fata error. .dat file has been copied" + 
            "to the submit folder")


def finalize_job(job_name,submit_dir):
    merge_res_files(job_name)

    #print("submit dir:" + submit_dir)
    #print("scratch_dir:" + os.getcwd())
    for ext in AbaqusConstants.OUTPUT_FILE_EXTENSIONS:
        shutil.copy2(os.path.join(os.getcwd(), job_name + ext), 
                                 submit_dir)
    print("Job is completed." + 
          "All output files has been copied back to the submit folder")
    
    
def look_for_include_files(input_file_name):
    additional_files = find_the_line('include','input',input_file_name)
    for line in additional_files:
        if line:
            line = line.replace('\n', '')
            line = line.split("=", 2)[1]
            #get rid of the first dot in the relative path
            split_path = line.replace('./', '').rsplit('/', 1)
            additional_file = split_path[-1]
            if len(split_path) > 1:
                relative_folder_path = split_path[0]
            else:
                relative_folder_path = ''   

            yield relative_folder_path, additional_file



def create_new_input_file(job_name, input_file_name, submit_dir, 
                          frequency):
    print("2nd condition")
    all_step_lines = get_step_lines(input_file_name) 

    with open(job_name + u'.sta', 'r') as sta_file:
        line_list = sta_file.readlines()

    if re.search('completed', line_list[-1], re.IGNORECASE):
        finalize_job(job_name, submit_dir)
        sys.exit()

    last_line = line_list[-1].split()
    last_step = last_line[0]
    last_increment = last_line[1]
    new_input_string = ('*Restart, read, step=' + last_step + 
                        ', inc=' + last_increment + 
                        ', write, overlay, frequency=' +  frequency)
    with open(u'Res_' + input_file_name, 'w') as new_input_file:
        new_input_file.write(u'*Heading\n')
        new_input_file.write(new_input_string + '\n')
        for step_lines in all_step_lines[int(last_step) :]:
            for line in step_lines:
                new_input_file.write(line)
                
def reserve_tokens(job_id):
    host = LicenseConstants.SLURM_CONTROL_SERVER
    port = LicenseConstants.LICENSE_MANAGER_PORT
    sock = socket.socket()
    sock.connect((host, port))
    sock.send(bytes(f'REQUEST {job_id}', 'utf-8'))

def release_tokens(job_id):
    host = LicenseConstants.SLURM_CONTROL_SERVER
    port = LicenseConstants.LICENSE_MANAGER_PORT
    sock = socket.socket()
    sock.connect((host, port))
    sock.send(bytes(f'REMOVE {job_id}', 'utf-8'))