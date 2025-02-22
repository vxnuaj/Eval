import logging
import colorlog

def setup_colored_log():
    '''
    sets up colored logging 
    '''
    
    log_format = '%(log_color)s%(asctime)s - %(levelname)s - %(message)s'
    
    formatter = colorlog.ColoredFormatter(
        log_format,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )

    console = colorlog.StreamHandler()
    console.setFormatter(formatter)

    logging.getLogger().addHandler(console)
    logging.basicConfig(level=logging.INFO, format=log_format) 