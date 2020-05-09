import cbf
import sys

if len(sys.argv) != 4:
    print("make_cbf.py: Make a cbf-wrapped leapfrog file.")
    print("Syntax: make_cbf.py <mem> <inpath> <outpath>")
    print("Mem options: low/high/superhigh")
    sys.exit(1)

cbf.create(mem=sys.argv[1], opath=sys.argv[3], ipath=sys.argv[2])
