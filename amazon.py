import os
import shutil
import sys
import time

os.chdir("/home/plumprint/Dropbox (Plum Print)/ARCHIVE/ARTWORK ARCHIVE")

f = open("amazon.%s.log" % time.time(), "w")

xs = os.listdir(".")[:32]

for i, x in enumerate(xs):
    if not os.path.isdir(x):
        f.write("SKIP %s\n\n" % x)
        continue
    if x == "Digitizing Only Files":
        continue
    print >> sys.stderr, i + 1, len(xs), x
    y = " ".join([
        "~/.local/bin/aws s3 mv",
        # "'%s'" % x.replace("'", "\\'"),
        # "'s3://plumprint-archive/ARTWORK/%s'" % x.replace("'", "\\'"),
        '"%s"' % x,
        '"s3://plumprint-archive/ARTWORK/%s"' % x,
        "--recursive",
        "--storage-class STANDARD_IA",
        #"--dryrun"
    ])
    f.write("%s\n" % y)
    print y
    if os.system(y):
        raise Exception("return != 0")
    # os.rmdir(x)
    shutil.rmtree(x)
    f.write("OK\n\n")
    
print "DONE (%s folders)" % len(xs)

