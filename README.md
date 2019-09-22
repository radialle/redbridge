# redbridge

A simple script which runs over a user-provided list of ports and IP
addresses trying to get a shell via adb. Uses Google's
[python-adb](https://github.com/google/python-adb) library. It is
recommended to use this tool within an isolated environment.

For research. Please use responsibly.

### Input file example

```
172.16.0.100:5555
172.16.0.105:5555
172.16.0.110:5555
172.16.0.115:5555
```

### Usage example

```
$ cat input.txt | python3 redbridge.py
```