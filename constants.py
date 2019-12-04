
class AbaqusConstants:
    FILE_EXTENSIONS =  [u'.res', u'.mdl', u'.stt', u'.prt', u'.sim',   
                        u'.com', u'.cid', u'.023', u'.dat', u'.msg', u'.sta']
    OUTPUT_FILE_EXTENSIONS = [u'.odb', u'.msg', u'.dat', u'.sta']
    BIN_LOCATION = u'/usrfem/femsys/abaqus/Commands/'
    SCRATCH_FOLDER = u'/Scratch_local/'               
    #SCRATCH_FOLDER = u'/usrfem/Scratch_global/'               

class LicenseConstants:
    LMUTIL_PATH = u'/usrfem/util/DIVERS/lmutil_linux'
    LICENSE_PATH = u'/usrfem/femsys/abaqus/abaqus_semcon.lic'
    SACCT_ABAQUS_LICENSE_SERVER_STRING = u'abaqus@se-got-lic01'
    ABAQUS_GRES_STRING = u'gres=license:abaqus:'
    LICENSE_MANAGER_PORT = 65432
    SLURM_CONTROL_SERVER = u'se-got-queue01'
    ABAQUS_CALC_SERVER = u'se-got-nc001'