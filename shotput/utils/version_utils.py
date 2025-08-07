
from pathlib import Path, PurePath

class VersionUtils:
    """
    Test
    vf = VersionUtils.getVersionFolders("Y:/PROJECTS/99991_cgDev/shots/sh010/publish/render/render2d_animDeadline")
    print (vf)
    print (VersionUtils.getVersionString(vf))
    """  
    versionStr = 'v'
    versionDefault = f'{versionStr}{1:03d}'
        
    @classmethod
    def getVersionFolders(cls, rootDir, latest=True, create_if_missing=False):
        """
        Get version folders from a directory.
        
        Args:
            rootDir: Path object to search
            latest: Return latest version if True
            create_if_missing: Create root directory if it doesn't exist (default False)
        """        
        versionDirs = []   
        vDefault = f'v{1:03d}'   

        # Only create directory if explicitly requested
        if create_if_missing and not rootDir.is_dir():
            rootDir.mkdir(parents=True, exist_ok=True) 
            
        if rootDir.is_dir():            
            for path in rootDir.iterdir():
                if path.is_dir():  
                    lastDir = PurePath(path).name 
                    if lastDir.startswith(cls.versionStr):                                     
                        versionDirs.append(lastDir)  
            if len(versionDirs) > 0 :
                versionDirs.sort(reverse=True)
                return versionDirs[0] if latest else versionDirs
            else:
                return None
        else:
            return None
           
    @classmethod
    def getVersionString(cls, version, up=True):
        # if we are passing an integer, we only ever want that version number

        if isinstance(version, int):
            return f'v{version:03d}'
        else:
            if version!= None:
                vNumber =  version.lstrip('v')
                vInt = int(vNumber)
                if up:
                    vInt +=1
                return f'v{vInt:03d}'
            else:
                return cls.versionDefault
            
    @classmethod
    def getVersionNumber(cls, str_version):
        if str_version!= None:
            vNumber =  str_version.lstrip('v')
            vInt = int(vNumber)
            return vInt
        else:
            return cls.versionDefault