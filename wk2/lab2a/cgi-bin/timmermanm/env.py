import os
for key in os.environ:
    print("{}: {}\n".format(key, os.environ[key]))
