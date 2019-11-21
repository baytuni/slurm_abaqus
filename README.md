# 
This project consists of 2 main parts. 

First part is a license manager to manage the licenses for slurm as
slurm does not manage abaqus licenses properly. License manager is a
class (see 'LicenseManager.py') which is instantiated by a daemon script
in SlurmLicenseManager.py which runs as a service by systemd.

Second part is abaqus_job_submission script takes advantage of application checkpointing. Reads the input files, moves files to scratch
folder and handles restarts. Also communicates with the license daemon
asks and release licenses.

