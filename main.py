import argparse

from make_chart import save


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-dpi', '--dots-per-inch', default=600, help='The output files resolution')
    parser.add_argument('-f', '--filename', default='table.png',
                        help='Output filename. For 3 files option index 1, 2, 3 is inserted before file extension.'
                             'Image compression is defined by extension, which is mandatory')

    args = parser.parse_args()
    args.single = True

    save(args.dots_per_inch, args.filename)

# TODO Tweak v_values, y_offsets, size, and x-position calculation to produce a nice chart. make it more dynamic
# TODO adjust size of canvas"
# TODO add big D on top line
