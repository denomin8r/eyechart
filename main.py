import argparse

from make_chart import save


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', default='table.png',
                        help='Output filename. For 3 files option index 1, 2, 3 is inserted before file extension.'
                             'Image compression is defined by extension, which is mandatory')

    args = parser.parse_args()

    save(args.filename)
