import sys
import os
import zlib
import hashlib


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    





    # Uncomment this block to pass the first stage
    
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
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
                
                if raw[i] == 0  and flag:
                    list.append(chunk)
                    chunk = b""
                    flag = False
                else:
                    chunk += bytes([raw[i]])
                if raw[i] == 32:
                    flag = True
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
                    ls[i-2].append(sha)
                    if i!=len(list)-1:
                        mdName = l[20:]
                        ls.append( mdName.split(b" ",maxsplit=1))
                
            for obj in ls:
                if(obj[0] == b"40000"):
                    tb = "tree" #tree/bloob
                else:
                    tb = "blob"
                print(f"{obj[0].decode()} {tb} {obj[2].hex()}\t{obj[1].decode()}")
        
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
