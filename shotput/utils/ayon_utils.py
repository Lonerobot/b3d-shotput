"""
AYON integration utilities for Shotput
Detects AYON environment and provides integration helpers
"""

import os

def is_ayon_environment():
    """Check if running in an AYON environment"""
    ayon_vars = [
        'AYON_PROJECT_NAME',
        'AYON_FOLDER_PATH', 
        'AYON_TASK_NAME',
        'AYON_WORKFILE_PATH',
        'AYON_SERVER_URL',
        'AYON_API_KEY'
    ]
    
    # Check if any AYON variables are present
    for var in ayon_vars:
        if os.environ.get(var):
            return True
    
    # Also check for OpenPype variables (AYON's predecessor)
    openpype_vars = [
        'OPENPYPE_PROJECT_ROOT_WORK',
        'OPENPYPE_CURRENT_PROJECT',
        'OPENPYPE_CURRENT_TASK'
    ]
    
    for var in openpype_vars:
        if os.environ.get(var):
            return True
            
    return False

def get_ayon_environment_info():
    """Get all AYON/OpenPype related environment variables"""
    env_info = {}
    
    # AYON variables
    ayon_vars = [
        'AYON_PROJECT_NAME',
        'AYON_FOLDER_PATH',
        'AYON_TASK_NAME',
        'AYON_TASK_TYPE',
        'AYON_VARIANT',
        'AYON_VERSION',
        'AYON_WORKFILE_PATH',
        'AYON_SERVER_URL',
        'AYON_API_KEY',
        'AYON_USERNAME',
        'AYON_CURRENT_CONTEXT'
    ]
    
    # OpenPype variables (for backward compatibility)
    openpype_vars = [
        'OPENPYPE_PROJECT_ROOT_WORK',
        'OPENPYPE_CURRENT_PROJECT',
        'OPENPYPE_CURRENT_TASK',
        'OPENPYPE_CURRENT_ASSET',
        'OPENPYPE_VERSION'
    ]
    
    # Collect AYON variables
    for var in ayon_vars:
        value = os.environ.get(var)
        if value:
            env_info[var] = value
    
    # Collect OpenPype variables
    for var in openpype_vars:
        value = os.environ.get(var)
        if value:
            env_info[var] = value
    
    return env_info

def get_ayon_project_info():
    """Get AYON project-specific information"""
    info = {
        'project_name': os.environ.get('AYON_PROJECT_NAME', ''),
        'folder_path': os.environ.get('AYON_FOLDER_PATH', ''),
        'task_name': os.environ.get('AYON_TASK_NAME', ''),
        'task_type': os.environ.get('AYON_TASK_TYPE', ''),
        'variant': os.environ.get('AYON_VARIANT', ''),
        'version': os.environ.get('AYON_VERSION', ''),
        'workfile_path': os.environ.get('AYON_WORKFILE_PATH', ''),
        
        # OpenPype fallbacks
        'openpype_project': os.environ.get('OPENPYPE_CURRENT_PROJECT', ''),
        'openpype_asset': os.environ.get('OPENPYPE_CURRENT_ASSET', ''),
        'openpype_task': os.environ.get('OPENPYPE_CURRENT_TASK', ''),
    }
    
    return {k: v for k, v in info.items() if v}  # Only return non-empty values

def get_ayon_render_path():
    """Generate AYON-compatible render path if in AYON environment"""
    if not is_ayon_environment():
        return None
        
    project_info = get_ayon_project_info()
    
    # Try to construct a path using AYON variables
    project_name = project_info.get('project_name') or project_info.get('openpype_project')
    folder_path = project_info.get('folder_path') or project_info.get('openpype_asset')
    task_name = project_info.get('task_name') or project_info.get('openpype_task')
    
    if project_name and folder_path and task_name:
        # Basic AYON path structure
        render_path = f"{{project}}/{folder_path}/work/{task_name}/renders/{{layer}}/{{pass}}"
        return render_path
    
    return None

def apply_ayon_defaults_to_shotput(shotput_props):
    """Apply AYON context to Shotput properties if available"""
    if not is_ayon_environment():
        return False
        
    project_info = get_ayon_project_info()
    changes_made = False
    
    # Set render layer from AYON task info
    task_name = project_info.get('task_name') or project_info.get('openpype_task')
    if task_name and not shotput_props.render_layer:
        shotput_props.render_layer = task_name
        changes_made = True
    
    # Set variant from AYON variant
    variant = project_info.get('variant')
    if variant and not shotput_props.variant:
        shotput_props.variant = variant
        changes_made = True
    
    # Set AYON-compatible root folder token
    ayon_path = get_ayon_render_path()
    if ayon_path and shotput_props.root_folder_token == "{project}/renders":
        shotput_props.root_folder_token = ayon_path
        changes_made = True
    
    return changes_made
