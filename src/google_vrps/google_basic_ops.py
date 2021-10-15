""" This module contains basic operations for using them with google or tools. """

from datetime import datetime


def write_solution_to_file(fpath, plan_output):
    """ Method to write the final solution to a file to disk.
    
    Args:
        fpath (str): Filepath where the solution is found.
        plan_output (str): Output of the solution found.'.
        total_time (str): total time of the trip'.
    """
    with open(fpath, 'a') as f:
        f.write(plan_output)


def create_results_name(path_to_disk='results/', postfix='.txt'):
    now = datetime.now()
    created_on = now.strftime(("%Y-%m-%d-%H-%M-%S"))
    results_name = path_to_disk + 'results_created_on_' + str(created_on) + postfix
    return results_name


def main():
    print("just special tools for read/write to a file.")


if __name__ == '__main__':
    main()