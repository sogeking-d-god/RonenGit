import os
import subprocess
import pytest

@pytest.fixture
def setup_git_directory(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)

def run_command(command):
    result = subprocess.run(command, capture_output=True, text=True)
    print(f"Command: {' '.join(command)}")
    print(f"Return code: {result.returncode}")
    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr}")
    return result

def test_init(setup_git_directory):
    main_py_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'main.py'))
    result = run_command(["python3", main_py_path, "init"])
    assert result.returncode == 0
    assert os.path.isdir(".git")
    assert os.path.isdir(".git/objects")
    assert os.path.isdir(".git/refs/heads")
    assert os.path.isfile(".git/HEAD")

def test_cat_file(setup_git_directory):
    main_py_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'main.py'))
    run_command(["python3", main_py_path, "init"])
    with open("testfile.txt", "w") as f:
        f.write("Hello, World!")
    result = run_command(["python3", main_py_path, "hash-object", "-w", "testfile.txt"])
    sha1 = result.stdout.strip()
    result = run_command(["python3", main_py_path, "cat-file", "-p", sha1])
    assert result.returncode == 0
    assert result.stdout.strip() == "Hello, World!"

def test_write_tree(setup_git_directory):
    main_py_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'main.py'))
    run_command(["python3", main_py_path, "init"])
    os.mkdir("testdir")
    with open("testdir/testfile.txt", "w") as f:
        f.write("Hello, World!")
    result = run_command(["python3", main_py_path, "write-tree"])
    assert result.returncode == 0
    assert "Stored tree:" in result.stdout

def test_commit_tree(setup_git_directory):
    main_py_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'main.py'))
    run_command(["python3", main_py_path, "init"])
    os.mkdir("testdir")
    with open("testdir/testfile.txt", "w") as f:
        f.write("Hello, World!")
    result = run_command(["python3", main_py_path, "write-tree"])
    tree_sha1 = result.stdout.strip().split()[-1]
    result = run_command(["python3", main_py_path, "commit-tree", tree_sha1, "-m", "Test commit"])
    assert result.returncode == 0
    assert "commit sha:" in result.stdout