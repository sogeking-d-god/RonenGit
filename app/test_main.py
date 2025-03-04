import os
import subprocess
import pytest

@pytest.fixture
def setup_git_directory(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)

def test_init(setup_git_directory):
    result = subprocess.run(["python3", "app/main.py", "init"], capture_output=True, text=True)
    assert result.returncode == 0
    assert os.path.isdir(".git")
    assert os.path.isdir(".git/objects")
    assert os.path.isdir(".git/refs/heads")
    assert os.path.isfile(".git/HEAD")

def test_cat_file(setup_git_directory):
    subprocess.run(["python3", "app/main.py", "init"], capture_output=True, text=True)
    with open("testfile.txt", "w") as f:
        f.write("Hello, World!")
    result = subprocess.run(["python3", "app/main.py", "hash-object", "-w", "testfile.txt"], capture_output=True, text=True)
    sha1 = result.stdout.strip()
    result = subprocess.run(["python3", "app/main.py", "cat-file", "-p", sha1], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "Hello, World!"

def test_write_tree(setup_git_directory):
    subprocess.run(["python3", "app/main.py", "init"], capture_output=True, text=True)
    os.mkdir("testdir")
    with open("testdir/testfile.txt", "w") as f:
        f.write("Hello, World!")
    result = subprocess.run(["python3", "app/main.py", "write-tree"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Stored tree:" in result.stdout

def test_commit_tree(setup_git_directory):
    subprocess.run(["python3", "app/main.py", "init"], capture_output=True, text=True)
    os.mkdir("testdir")
    with open("testdir/testfile.txt", "w") as f:
        f.write("Hello, World!")
    result = subprocess.run(["python3", "app/main.py", "write-tree"], capture_output=True, text=True)
    tree_sha1 = result.stdout.strip().split()[-1]
    result = subprocess.run(["python3", "app/main.py", "commit-tree", tree_sha1, "-m", "Test commit"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "commit sha:" in result.stdout