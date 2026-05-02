#!/usr/bin/env python
"""Entry point for protein validation.

This thin wrapper preserves the required runnable form:

    python validate.py /path/to/pdbs --out results.csv
"""

from submission.validate import main


if __name__ == '__main__':
    main()
