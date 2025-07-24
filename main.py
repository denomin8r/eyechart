import argparse

from make_chart import EyeChart


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--single', action='store_true', help='Single file, or 3 files to be printed on A4')
    parser.add_argument('-dpi', '--dots-per-inch', default=600, help='The output files resolution')
    parser.add_argument('-f', '--filename', default='table.png',
                        help='Output filename. For 3 files option index 1, 2, 3 is inserted before file extension.'
                             'Image compression is defined by extension, which is mandatory')

    args = parser.parse_args()
    args.single = True

    table = EyeChart()
    table.save(args.dots_per_inch, args.filename, args.single)
