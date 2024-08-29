## CCC Tools

Utility tools for Conda Compute Cluster

# Distributed run
Run your script distributed on servers

`ccc run [your script] [args]` 

e.g.: `ccc run python train.py --config epoch=10` 

# Find gpus

Find available gpus that you can use for distributed running

`ccc gpus [ARGS]` 

e.g.: `ccc gpus --on_cluster=my_cluster_info.json  --gpus=2 --tasks=4 --hosts="hostname1,hostname2(1+3),hostname3(1+2)" --ignore_hosts="hostname4"