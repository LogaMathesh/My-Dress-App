"""
Python script to start Celery worker.
Use this if 'celery' command is not recognized.
"""
import subprocess
import sys
import os

def main():
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    print("Starting Celery Worker for async image processing...")
    print()
    print("Make sure Redis is running on localhost:6379")
    print()
    
    try:
        # Use python -m celery instead of celery command
        subprocess.run([
            sys.executable, '-m', 'celery',
            '-A', 'celery_worker.celery_app',
            'worker',
            '--pool=solo',
            '--loglevel=info'
        ])
    except KeyboardInterrupt:
        print("\nStopping Celery worker...")
    except Exception as e:
        print(f"Error starting Celery worker: {e}")
        print("\nMake sure:")
        print("1. Celery is installed: pip install celery")
        print("2. Redis is running")
        print("3. You're in the backend directory")

if __name__ == '__main__':
    main()





