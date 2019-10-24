#!/usr/bin/env python3 

import sys
import os
import re
import shutil
import fnmatch
import getpass


class AbaqusConstants:
    FILE_EXTENSIONS =  [u'.res', u'.mdl', u'.stt', u'.prt', u'.sim',   
                        u'.com', u'.cid', u'.023', u'.dat', u'.msg', u'.sta']
    OUTPUT_FILE_EXTENSIONS = [u'.odb', u'.msg', u'.dat', u'.sta']
    BIN_LOCATION = u'/usrfem/femsys/abaqus/Commands/'
    SCRATCH_FOLDER = u'/usrfem/Scratch_global/'               


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
Generic function to delete  or move all the files from a given 
directory based on matching pattern
'''
def wildcard_operations(sourcePath, pattern, 
                        operation='remove', targetPath=None):
    listOfFilesWithError = []
    for parentDir, dirnames, filenames in os.walk(sourcePath):
        for filename in fnmatch.filter(filenames, pattern):
            try:
                if operation == 'remove':
                    os.remove(os.path.join(parentDir, filename))
                if operation == 'move' and targetPath:
                    shutil.move(os.path.join(parentDir, filename), 
                                targetPath)
            except:
                print("Error while deleting file : ", 
                     os.path.join(parentDir, filename))
                listOfFilesWithError.append(os.path.join(parentDir, filename))
    return listOfFilesWithError

    
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


def restart_join(abaqus_version, job_name):
        cmd_to_run = (AbaqusConstants.BIN_LOCATION  + 'abq' + abaqus_version + 
                      u' restartjoin originalodb=' + job_name +
                      u' restartodb=Res_' + job_name + u' history')
        os.system(cmd_to_run)
    

def finalize_job(job_name,submit_dir):
    print("Job is completed. Residual files will be cleared")

    merge_res_files(job_name)

    for ext in AbaqusConstants.OUTPUT_FILE_EXTENSIONS:
        wildcard_operations(os.curdir, ext, 
                            operation='move', targetPath=submit_dir)
    
    
def look_for_include_files(input_file_name):
    pass


if __name__ == "__main__":
    print(sys.argv)
    #This env variable has to be unset in order abaqus to run.
    if 'SLURM_GTIDS' in os.environ:
        del os.environ['SLURM_GTIDS']
    
    #Get slurm env variables
    submit_dir = sys.argv[1]
    #Get the input file name
    job_name = sys.argv[2]
    input_file_name = job_name + '.inp'
    slurm_job_id = sys.argv[3]
    slurm_ntasks = sys.argv[4]
    abaqus_version = sys.argv[5]
    
    user_name = getpass.getuser()
    job_folder_name = slurm_job_id + '_' + job_name + '_' + user_name 
    
    # Search and find the checkpointing line in the input file.  
    #If found save the frequency value.
    restart_line = find_the_line('\*restart', 'frequency', input_file_name)
    if restart_line:
        restart_line = next(restart_line)
        search_object = re.search(r'\d+', restart_line.split("=",2)[1])
        if search_object:
            frequency = search_object.group()
        else:
            raise Exception(('Check {} file and make sure the line ' 
                            'starting with \"*Restart,\" is there and '
                            'settings are correct').format(input_file_name))

    # If there is no folder in the scratch_dir, make one and copy
    #the input file
    if not os.path.isdir(AbaqusConstants.SCRATCH_FOLDER + job_folder_name):
        os.mkdir(AbaqusConstants.SCRATCH_FOLDER + job_folder_name)
        shutil.copy(input_file_name, AbaqusConstants.SCRATCH_FOLDER + 
                    job_folder_name)
        #Read additional files from the file and copy them to scratch
        additional_files = find_the_line('include','input',input_file_name)
        for line in additional_files:
            if line:
                additional_file = line.split("=",2)[1].split("inp",2)[0] + "inp"
                print(additional_file)
                shutil.copy(additional_file, AbaqusConstants.SCRATCH_FOLDER + 
                            job_folder_name)
                
    #cd in the scratch folder
    os.chdir(AbaqusConstants.SCRATCH_FOLDER + job_folder_name)

    # If there the job has been already restarted at least once 
    #move the Res_ files to original files and join odbs
    if os.path.isfile('Res_' + job_name + '.sta'):
        print("1st condition")
        wildcard_operations(os.curdir,'*.lck', operation='remove')  
        restart_join(abaqus_version, job_name)
        merge_res_files(job_name)

    if os.path.isfile(job_name + '.sta'):

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


        cmd_to_run = (AbaqusConstants.BIN_LOCATION  + 
                      u'abq' + abaqus_version + u' job=Res_' + job_name +
                      u' input=Res_' + input_file_name  + 
                      u' oldjob=' + job_name + u' cpus=' + slurm_ntasks +
                      u' -verbose 3 standard_parallel=all mp_mode=mpi interactive')
        print(cmd_to_run)
        os.system(cmd_to_run)

    else:
        print("3rd Condition")
        cmd_to_run = (AbaqusConstants.BIN_LOCATION  + 
                      u'abq' + abaqus_version + u' job=' + job_name +
                      u' input=' + input_file_name + 
                      u' oldjob=' + job_name + u'cpus=' + slurm_ntasks +
                      u' -verbose 3 standard_parallel=all mp_mode=mpi interactive')
        os.system(cmd_to_run)

    # If the job is completed, search for a specific string in the job file
    res_msg_file_name = u'Res_' + job_name + u'.msg'        
    msg_file_name = job_name + u'.msg'        
    if  os.path.isfile(res_msg_file_name):
        msg_file_name = res_msg_file_name
    if os.path.isfile(msg_file_name):
        if next(find_the_line('the analysis','has been completed',
                              msg_file_name)):
            finalize_job(job_name,submit_dir)
    else:
        print("No message file has been found. The analysis has probably " +
              "never been run!")

    sys.exit()
