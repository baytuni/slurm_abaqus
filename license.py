import os
import re
import subprocess
class LicensePaths:
    LMUTIL = '/usrfem/util/DIVERS/lmutil_linux'
    LICENSE_FILE = '/usrfem/femsys/abaqus/abaqus_semcon.lic'


if __name__ == '__main__':

    license_stream = subprocess.check_output(LicensePaths.LMUTIL, 'lmstat',
                                             '-c', LicensePaths.LICENSE_FILE,
                                             '-a')
