import os

def check_and_create_dirs(base_dir='tmp'):
    """
    Checks for the existence of directories: tmp, tmp/clips, and tmp/raw.
    Creates them if they do not exist.
    
    Parameters:
        base_dir (str): The base directory to use. Defaults to 'tmp'.
    """
    required_paths = [
        base_dir,
        os.path.join(base_dir, 'clips'),
        os.path.join(base_dir, 'raw')
    ]
    
    for path in required_paths:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            print(f"Created directory: {path}")
        else:
            print(f"Directory already exists: {path}")

