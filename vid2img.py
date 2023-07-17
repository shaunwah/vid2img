import argparse

from functions import process_batch

parser = argparse.ArgumentParser(prog="vid2img")
parser.add_argument("input", type=str, help="the input file/directory to be processed")
parser.add_argument("--sorted", action="store_true", help="sorts input directory by name")
parser.add_argument("-o", "--output", type=str, help="the output directory")
parser.add_argument("--rows", type=int, default=5, help="number of rows of generated thumbnails")
parser.add_argument("--columns", type=int, default=4, help="number of columns of generated thumbnails")
parser.add_argument("--delay", type=int, default=0, help="adds a delay to the first thumbnail")
parser.add_argument("--offset", type=int, default=0, help="adds an offset to all thumbnails")
parser.add_argument("--resize", type=int, default=100, help="resizes thumbnails (1-100 percent)")
parser.add_argument("--limit", type=int, default=-1, help="maximum files to be processed")
parser.add_argument("--override", action="store_true", help="overrides existing content")
parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
args = parser.parse_args()

process_batch(args)
