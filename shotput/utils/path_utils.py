import os 
from pathlib import Path

from .log import LoggerFactory
logger = LoggerFactory.logger_obj()

"""
UPDATED TO FUNCTION WITHIN AYON PIPELINE
"""

class PathUtils: 
     
    def get_user(self):
        return os.getenv("USERNAME")
    
    def get_project_path(self):
        open_pype_server_root = os.getenv("AYON_PROJECT_ROOT_WORK") 
        open_pype_project = os.getenv("AYON_PROJECT")
        
        if open_pype_server_root and open_pype_project:  
            project_path = Path() / open_pype_server_root / open_pype_project
            logger.debug(f'PathUtils.get_project_path - {project_path}')
            return str(project_path)
        else:
            return ""
 
    def get_work_path(self): 
        return os.getenv("AYON_WORKDIR")
         
    def get_project_name(self): 
        return os.getenv("AYON_PROJECT_NAME")

    def get_task_name(self):
        return os.getenv("AYON_TASK_NAME")

    # renamed to make more sense in the AYON env
    def get_folder_path(self):
        return os.getenv("AYON_FOLDER_PATH")