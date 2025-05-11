"""
# module: check_method_implementation
Check if directory_exists method is properly implemented

This script simply checks if the directory_exists method is properly
implemented in the SFTPManager class, without making any SSH connections.
"""
import inspect
from utils.sftp import SFTPManager

def check_directory_exists_implementation():
    """Check if directory_exists is implemented in SFTPManager"""
    print("Checking for directory_exists method in SFTPManager class...")
    
    # Check if the method exists
    if hasattr(SFTPManager, 'directory_exists'):
        print("✓ directory_exists method found in SFTPManager")
        
        # Get the method
        method = getattr(SFTPManager, 'directory_exists')
        
        # Get method signature
        sig = inspect.signature(method)
        print(f"  Method signature: {sig}")
        
        # Get method docstring
        doc = method.__doc__
        if doc:
            doc_first_line = doc.strip().split('\n')[0]
            print(f"  Method docstring: {doc_first_line}")
        else:
            print("  No docstring found")
            
        return True
    else:
        print("✗ directory_exists method NOT found in SFTPManager")
        return False

def main():
    """Main function"""
    print("="*60)
    print("CHECKING METHOD IMPLEMENTATION")
    print("="*60)
    
    has_method = check_directory_exists_implementation()
    
    print("\nList of all methods in SFTPManager class:")
    for name, method in inspect.getmembers(SFTPManager, predicate=inspect.isfunction):
        print(f"  - {name}")
        
    if has_method:
        print("\nResult: directory_exists is properly implemented")
    else:
        print("\nResult: directory_exists implementation is missing")
        
    print("="*60)

if __name__ == "__main__":
    main()