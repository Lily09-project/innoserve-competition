"""Retired renderer: refuse output rather than substitute unapproved fonts."""
import sys


def main():
    print('This renderer is retired: it cannot guarantee DFKai-SB and Times New Roman. '
          'Use node scripts/render_product_film.mjs NEW_OUTPUT_DIRECTORY with the required fonts installed.',
          file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
