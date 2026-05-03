import logging
logging.basicConfig(filename = 'pipeline.log', level = logging.DEBUG, filemode = 'a', format = '%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pipeline.log')


def LOGGER_FUNCTION(dtype,msg):


    match dtype:
        case 'info': logger.info(f"{msg}")
        case 'debug': logger.debug(f"{msg}")
        case 'warning': logger.warning(f"{msg}")
        case 'error': logger.error(f"{msg}")
        case 'critical': logger.critical(f"{msg}")
        case _ : logger.info(f"{msg}")


#logging.basicConfig() should not be called inside a wrapper function 
# every time you want to log a message. The correct design is to configure 
# the logger once, usually in one helper function, and then reuse that 
# logger object across modules so your logs stay consistent and your code 
# stays simpler.