# 
This project consists of 2 main parts:

*First part is a license updater to update slurm of licenses using flexlm license manager.
This script is running as a crontab job running every 2 hours  

*Second part is abaqus_job_submission is used for abaqus jobs only. It takes care of copying files 
to scratch folder and copying back the results. All the paths are defined at "constants.py" file as 
constant classes.
It also takes advantage of application checkpointing if the job is submitted to slurm partitions(queues)
that have "REQUEUE" as preemption method. Application checkpointing means to use abaqus's checkpoint/restart
feature. The input files need to be parsed and some parts need to be copied to a new input file everytime 
the queue restarts.



