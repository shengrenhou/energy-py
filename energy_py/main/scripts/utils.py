import csv
import itertools
import pickle
import os
import time

import numpy as np


class Utils(object):
    """
    A base class that holds generic functions
    """
    def __init__(self, verbose=0):
        self.verbose = verbose

    """
    Useful Python functions:
    """

    def verbose_print(self, *args, level=1):
        """
        Helper function to print info.

        self.verbose = 0 & level = 0 -> print 
        self.verbose = 0 & level = 1 -> no printing
        self.verbose = 1 & level = 1 -> printing

        level=0 -> always print
        level=1 -> normal print level
        level=2 -> debugging

        args
            *args : arguments to be printed
            level : the level of the args

        """
        if self.verbose >= level:
            [print(a) for a in args]
        return None

    def dump_pickle(self, obj, name):
        with open(name, 'wb') as handle:
            pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def load_pickle(self, name):
        with open(name, 'rb') as handle:
            obj = pickle.load(handle)
        return obj

    def ensure_dir(self, file_path):
        """
        Check that a directory exists
        If it doesn't - make it
        """
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def get_upper_path(self, string):
        owd = os.getcwd()  #  save original working directory
        os.chdir(string)  #  move back two directories
        base = os.getcwd()  #  get new wd
        os.chdir(owd)  #  reset wd
        return base

    def save_args(self, argparse, path, optional={}):
        """
        Saves args from an argparse object and from an optional
        dictionary

        args
            argparse (object) 
            path (str)        : path to save too
            optional (dict)   : optional dictionary of additional arguments

        returns
            writer (object) : csv Writer object
        """
        with open(path, 'w') as outfile:
            writer = csv.writer(outfile)
            for k, v in vars(argparse).items():
                print('{} : {}'.format(k, v))
                writer.writerow([k]+[v])

            if optional:
                for k, v in optional.items():
                    print('{} : {}'.format(k, v))
                    writer.writerow([k]+[v])
        return writer

    """
    energy_py specific functions 
    """

    def normalize(self, value, low, high):
        """
        Generic helper function
        Normalizes a value using a given lower & upper bound

        args
            value (float)
            low   (float) : upper bound
            high  (float) : lower_bound

        returns
            normalized (np array)
        """
        #  if statement to catch the constant value case
        if low == high:
            normalized = 0
        else:
            max_range = high - low
            normalized = (value - low) / max_range
        return np.array(normalized)

    def scale_array(self, array, space):
        """
        Helper function for make_machine_experience()
        Uses the space & a given function to scale an array
        Scaling is done by normalization 

        Used to scale the observations and actions

        args
            array (np array) : array to be scaled
                               shape=(1, space_length)

            space (list) : a list of energy_py Space objects
                           shape=len(action or observation space)

        returns
            scaled_array (np array)  : the scaled array
                                       shape=(1, space_length)
        """
        array = array.reshape(-1)
        assert array.shape[0] == len(space)

        #  iterate across the array values & corresponding space object
        for value, spc in itertools.zip_longest(array, space):
            if spc.type == 'continuous':
                # normalize continuous variables
                scaled = self.normalize(value, spc.low, spc.high)
            elif spc.type == 'discrete':
                #  shouldn't need to do anything
                #  check value is already dummy
                assert (value == 0) or (value == 1)
            else:
                assert 1 == 0

            scaled_array = np.append(scaled_array, scaled)

        return scaled_array.reshape(1, len(space))
