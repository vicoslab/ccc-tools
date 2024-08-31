import sys,os
import time
if __name__ == "__main__":
    print(sys.argv, "MY IMPORTED ENVS: ", {k:v for k,v in os.environ.items() if k in ['DATASET', 'USE_DEPTH', 'MY_CONFIG_ENV']} )
    time.sleep(5)