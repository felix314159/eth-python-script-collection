import os

def get_filepaths_python(basedir, max_allowed_chars_per_line, verbose):
    basedir_fullpath = os.path.abspath(basedir)

    # remember each file in which you have to fix at least one line
    # each element is a tuple (absolute_path, amountOfLinesThatNeedFixing)
    files_that_need_fixing = []
    for dirpath, dirnames, filenames in os.walk(basedir):
        for f in filenames:
            # get absolute path to file
            relative_path = os.path.join(dirpath, f)
            absolute_path = os.path.abspath(relative_path)

            # skip files that are not .py
            _, file_extension = os.path.splitext(absolute_path)
            if not file_extension == ".py":
                continue

            # read file into list of line lengths
            with open(absolute_path, 'r') as file:
                line_length = [len(line.strip()) for line in file]

            # determine amount of line length violations for this file
            amt_violations = 0
            for l in line_length:
                if l > max_allowed_chars_per_line:
                    amt_violations += 1

            if amt_violations > 0:
                files_that_need_fixing.append((absolute_path, amt_violations))
                if verbose:
                    print(
                        f"File: {absolute_path}\n"
                        f"Amount of lines to fix: {amt_violations}\n"
                    )

    print(
        f"Total amount of files that need fixing: {len(files_that_need_fixing)}\n"
        f"Total amount of lines that need to be fixed: "
        f"{sum(l for _, l in files_that_need_fixing)}"
    )

def main():
    cwd = "."
    max_allowed_chars_per_line = 79
    verbose = False

    get_filepaths_python(cwd, max_allowed_chars_per_line, verbose)


main()
