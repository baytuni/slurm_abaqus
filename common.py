import os
import re
import shutil
import fnmatch
import subprocess
import time 

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
    additional_files = find_the_line('include','input',input_file_name)
    for line in additional_files:
        if line:
            additional_file = line.split("=",2)[1].split("inp",2)[0] + "inp"
            yield additional_file



