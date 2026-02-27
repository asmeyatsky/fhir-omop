"""Root conftest — sets environment for all tests."""
import os

os.environ["STORAGE_BACKEND"] = "memory"
