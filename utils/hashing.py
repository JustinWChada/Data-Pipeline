from config import *
from utils.logger import LOGGER_FUNCTION
from utils.config_log import CONFIG_LOGGER
from pathlib import Path, PurePath 
import hashlib
import io

#1
#but the implementation should open files in binary mode rather than 
# reading text and re-encoding to UTF-8, because file hashing should be 
# based on the raw bytes of the file, not on text interpretation.

#2
#Right now you redefine the SQLAlchemy Registry model separately inside 
# both STORE_REGISTRY_RECORD and FETCH_REGISTRY_RECORD, which is not a good 
# pattern.
CONFIG_LOGGER()

def HASHING_FUNCTION(filepath): 
    filename = str(PurePath(filepath).name)
    # filepath = str(PurePath(file))
    # print(filepath)
    #instead of filename, you can pass the entire file path to 
    # avoid searching for the file again in the directory structure. This will make the function more efficient and straightforward.
    hasher = hashlib.sha256()
    # p = Path('./')

    try:
        #q = list(p.glob(f"**/{filename}"))
    
        # filepath = pathlib.Path(filename)
        #filepath = str(PurePath(q.pop()))
        
        with open(filepath, 'rb') as f:
            #write log here
            LOGGER_FUNCTION('info', f"Hashing file: {filename}")
            
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
                
            digest = hasher.hexdigest()

            LOGGER_FUNCTION('info', f"Hashing completed for file {filename}")
            return digest #(filename, filepath, )

    except Exception as e:
        LOGGER_FUNCTION('error', f"An error occurred while hashing file {filename}: {e}")
        LOGGER_FUNCTION('warning', f"Hashing for the file {filename} is SKIPPED. Continuing with the next file.")
        return None

#unused, remove at deploy
def compute_sha256_hash(file_path: Path) -> str:
    sha256 = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)

            return sha256.hexdigest()
    except Exception as e:
        LOGGER_FUNCTION('error', f"Error computing hash for file {file_path}. Error: {str(e)}")
        return None