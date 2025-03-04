import sys
import os
import zlib
import hashlib
import time

def commit_tree(tree_sha1, message="Initial commit"):

    # Get author and committer info
    author_name = os.getenv("GIT_AUTHOR_NAME", "Your Name")
    author_email = os.getenv("GIT_AUTHOR_EMAIL", "your.email@example.com")

    # Get current timestamp in Git format
    timestamp = int(time.time())
    timezone_offset = time.strftime('%z')
    author_info = f"{author_name} <{author_email}> {timestamp} {timezone_offset}"

    # Read the current branch from .git/HEAD
    head_path = ".git/HEAD" 
    with open(head_path, "r") as f:
        ref_line = f.read().strip()
        if ref_line.startswith("ref: "):
            branch_ref = ref_line[5:]  # Extract refs/heads/<branch>
        else:
            branch_ref = None  # Detached HEAD (direct SHA-1 reference)
            print("error: Detached HEAD")
            return 
  
    # Read parent commit from the branch reference (if it exists)
    parent_sha1 = None
    branch_path = f".git/{branch_ref}"
    if os.path.exists(branch_path): # if not new branch
        with open(branch_path, "r") as f:
            parent_sha1 = f.read().strip()

    # Construct commit content
    commit_content = f"tree {tree_sha1}\n"
    if parent_sha1:
        commit_content += f"parent {parent_sha1}\n"
    commit_content += f"author {author_info}\n"
    commit_content += f"committer {author_info}\n\n"
    commit_content += f"{message}\n"

    # Compute SHA-1 hash
    store = f"commit {len(commit_content)}\0".encode() + commit_content.encode()
    commit_sha1 = hashlib.sha1(store).hexdigest()

    # Save commit object
    obj_path = f".git/objects/{commit_sha1[:2]}/{commit_sha1[2:]}"
    os.makedirs(os.path.dirname(obj_path), exist_ok=True)
    with open(obj_path, "wb") as f:
        f.write(zlib.compress(store))

    # Update branch reference to point to the new commit
    with open(f".git/{branch_ref}", "w") as f:
        f.write(commit_sha1 + "\n")

    print("message: \t" + message)
    return commit_sha1  # Return the commit SHA-1

    

def tree_w(dir_path):
    
    obj_sha1 = []    # To store the sha1 for all objects in the current directory


    # Process files and subdirectories in the current directory
    for file_or_dir in os.listdir(dir_path):


        # Skip .git directory
        if file_or_dir != ".git":
            full_path = os.path.join(dir_path, file_or_dir)
            # Process files
            if os.path.isfile(full_path):  # If it's a file

                with open(full_path, "rb") as f:
                    content = f.read()

                # Normalize Windows line endings to LF
                content = content.replace(b"\r\n", b"\n")

                # Store file as a blob
                header = f"blob {len(content)}\0".encode()
                store = header + content
                sha1 = hashlib.sha1(store).hexdigest()

                # Save blob to .git/objects
                os.makedirs(f".git/objects/{sha1[:2]}", exist_ok=True)
                with open(f".git/objects/{sha1[:2]}/{sha1[2:]}", "wb") as f:
                    f.write(zlib.compress(store))

                # Add file's sha1 to the list
                obj_sha1.append((file_or_dir, sha1, b"100644"))

            # Process subdirectories (handle them as tree objects)
            else:
                dir_sha1 = tree_w(full_path)  # Recursively process subdirectories
                obj_sha1.append((file_or_dir, dir_sha1, b"040000"))  # Add the directory's sha1 to the list
            


    # Now, create the tree object for the current directory
    tree_object = b""
    
    obj_sha1 = sorted(obj_sha1, key=lambda x: x[0])  # Sort objects by name

    for name, sha1, mode in obj_sha1:
        tree_object += mode + b" " + name.encode() + b"\0" + bytes.fromhex(sha1)

    
    # Create and store the tree object
    header = f"tree {len(tree_object)}\0".encode()
    store = header + tree_object
    sha1 = hashlib.sha1(store).hexdigest()

    # Save tree to .git/objects
    os.makedirs(f".git/objects/{sha1[:2]}", exist_ok=True)
    with open(f".git/objects/{sha1[:2]}/{sha1[2:]}", "wb") as f:
        f.write(zlib.compress(store))

    
    # Return the sha1 of the current directory's tree
    return sha1



def main():
    
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        os.mkdir(".git/refs/heads")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")

    elif command == "cat-file" and sys.argv[2] == "-p":
        obj_name = sys.argv[3]
        with open(f".git/objects/{obj_name[:2]}/{obj_name[2:]}", "rb") as f:
            raw = zlib.decompress(f.read())
            header, content = raw.split(b"\0", maxsplit=1)
            print(content.decode(encoding="utf-8"), end="")

    elif command == "hash-object" and sys.argv[2] == "-w":
        file_path = sys.argv[3]
        with open(file_path, "rb") as f:
            content = f.read()

        # Normalize Windows line endings to LF
        content = content.replace(b"\r\n", b"\n")

        header = f"blob {len(content)}\0".encode()
        store = header + content
        sha1 = hashlib.sha1(store).hexdigest()
        os.makedirs(f".git/objects/{sha1[:2]}", exist_ok=True)
        with open(f".git/objects/{sha1[:2]}/{sha1[2:]}", "wb") as f:
            f.write(zlib.compress(store))
        print(sha1)
    
    elif command == "ls-tree" and sys.argv[2] == "--name-only":
        obj_name = sys.argv[3]
        with open(f".git/objects/{obj_name[:2]}/{obj_name[2:]}", "rb") as f:
            raw = zlib.decompress(f.read())
            list = raw.split(b"\0")
            header= list[0].split(b" ",maxsplit=1)
            if header[0] != b"tree":
                print("Not a tree object")
                return
            for i in range(1, len(list)-1):
                if i!=2 :
                    name = list[i].split(b" ",maxsplit=1)
                    print(name[1].decode(encoding="utf-8"))
    
    elif command == "ls-tree":
        obj_name = sys.argv[2]
        with open(f".git/objects/{obj_name[:2]}/{obj_name[2:]}", "rb") as f:
            raw = zlib.decompress(f.read())
            list = []
            chunk = b""
            flag = False
            for i in range(0, len(raw)):
                
                if raw[i] == ord("\0")  and flag:
                    list.append(chunk)
                    chunk = b""
                    flag = False
                else:
                    chunk += bytes([raw[i]])
                if raw[i] == ord(" "):
                    flag = True
            list.append(chunk)

            header= list[0].split(b" ",maxsplit=1)
            if header[0] != b"tree":
                print("Not a tree object")
                return
            ls = []
            for i in range(1, len(list)):
                if i==1:
                    ls.append( list[i].split(b" ",maxsplit=1))
                else:
                    l = list[i]
                    sha = l[0:20]
                    ls[-1].append(sha)
                    if i!=len(list)-1:
                        mdName = l[20:]
                        ls.append( mdName.split(b" ",maxsplit=1))

            for obj in ls:
                if(obj[0] == b"040000"):
                    tb = "tree" #tree/bloob
                else:
                    tb = "blob"
                print(f"{obj[0].decode()} {tb} {obj[2].hex()}\t{obj[1].decode()}")
    
    elif command == "write-tree":
            print(f"Stored tree: {tree_w(os.getcwd())}")
        
    elif command == "commit-tree":
        if len(sys.argv) == 5 and sys.argv[3] == "-m":  
            print("commit sha: \t" + commit_tree(sys.argv[2], sys.argv[4]) ) # With message
        else: 
            print("commit sha: \t" + commit_tree(sys.argv[2]) ) # Without message


    else:
        raise RuntimeError(f"Unknown command #{command}")



if __name__ == "__main__":
    main()
