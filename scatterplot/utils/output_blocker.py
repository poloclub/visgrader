import sys
import os


"""This class is used to redirect stdout to null.  Used to block students from printing out server / variables during testing"""
class NoStd:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
