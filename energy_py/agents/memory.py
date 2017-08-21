"""

"""

import collections
import itertools
import os

import numpy as np
import pandas as pd

from energy_py.main.scripts.utils import ensure_dir
from energy_py.main.scripts.visualizers import Agent_Memory_Visualizer

class Agent_Memory(Agent_Memory_Visualizer):
    """
    inherits from Visualizer!

    A class to hold the memory of an agent

    Contains functions to process the memory for an agent to learn from
    """
    def __init__(self, memory_length,
                       observation_space,
                       action_space,
                       reward_space,
                       discount_rate):

        super().__init__()
        self.memory_length     = memory_length
        self.observation_space = observation_space
        self.action_space      = action_space
        self.reward_space      = reward_space
        self.discount_rate   = discount_rate

        #  a named tuple to hold experience
        self.Experience = collections.namedtuple('experience', 'observation, action, reward, next_observation, step, episode')
        self.Scaled_Experience = collections.namedtuple('experience', 'observation, action, reward, next_observation, step, episode, discounted_return')

        self.training_data = []  #  TODO

        self.reset()

    def reset(self):
        """
        Resets the memory object
        """
        self.experiences        = []
        self.scaled_experiences = []
        self.discounted_returns = np.array([])
        self.outputs  = collections.defaultdict(list)
        self.losses = []

    def normalize(self, value, low, high):
        """
        Helper function
        Normalizes a value
        """
        #  if statement to catch the constant value case
        if low == high:
            normalized = 0
        else:
            max_range = high - low
            normalized = (value - low) / max_range
        return np.array(normalized)

    def scale_array(self, array, space, scaler_fctn=normalize):
        """
        Helper function for scale_experience()
        Uses the space & a given function to scale an array
        Default scaler is to normalize

        Used to scale the observation and action
        """
        #  empty numpy array
        scaled_array = np.array([])
        #  iterate across the array values & corresponding space object
        for value, spc in itertools.zip_longest(array, space):
            #  use the fctn to transform the array
            scaled = scaler_fctn(value,
                                 spc.low,
                                 spc.high)
            #  appending the scaled value onto the scaled array
            scaled_array = np.append(scaled_array, scaled)
        assert array.shape == scaled_array.shape
        return scaled_array

    def scale_reward(self, reward, space, scaler_fctn=normalize):
        """
        Helper function for scale_experience()
        Uses a space to scale the reward
        """
        return scaler_fctn(reward, space.low, space.high)

    def scale_experience(self, exp, discounted_return=None):
        """
        Helper function for add_experience
        Scales a given experience tuple

        Discounted return is an optimal arg so that the scaled_exp array can
        be created at any time
        """
        #  here I do it a simple way - scaling the observation
        scaled_obs = self.scale_array(exp.observation, self.observation_space, self.normalize)
        #  scaling the action
        scaled_action = self.scale_array(exp.action, self.action_space, self.normalize)
        #  scaling the reward
                #  now we scale the next observation
        if exp.next_observation is False:
            scaled_next_observation = False
            scaled_reward = 0 
        else:
            scaled_next_observation = self.scale_array(exp.next_observation, self.observation_space, self.normalize)
            scaled_reward = self.scale_reward(exp.reward, self.reward_space, self.normalize)

        #  making a named tuple for the scaled experience
        scaled_exp = self.Scaled_Experience(scaled_obs,
                                            scaled_action,
                                            scaled_reward,
                                            scaled_next_observation,
                                            exp.step,
                                            exp.episode,
                                            discounted_return)
        return scaled_exp

    def add_experience(self, observation, action, reward, next_observation, step, episode):
        """
        Adds a single step of experience to the two experiences lists
        """
        exp = self.Experience(observation, action, reward, next_observation, step, episode)
        self.experiences.append(exp)

        scaled_exp = self.scale_experience(exp)
        self.scaled_experiences.append(scaled_exp)
        return None

    def process_episode(self, episode_number):
        """
        Calculates the discounted returns

        Should only be done once a episode is finished - TODO a check
        """
        print('agent memory is processing episode experience')
        old_experiences = [exp for exp in self.scaled_experiences if exp.episode == episode_number]

        #  we now reprocess our scaled experiences
        print('calculating discounted returns')
        for i, exp in enumerate(old_experiences):
            discounted_return = sum(self.discount_rate**j * exp.reward for j, exp in enumerate(old_experiences[i:]))

            scaled_exp = self.Scaled_Experience(exp.observation,
                                   exp.action,
                                   exp.reward,
                                   exp.next_observation,
                                   exp.step,
                                   exp.episode,
                                   discounted_return)

            idx = -(len(old_experiences) - i)
            self.scaled_experiences[idx] = scaled_exp

        assert len(self.experiences) == len(self.scaled_experiences)

        return None

    def get_batch(self, batch_size):
        """
        Gets a random batch of experiences.
        """

        sample_size = min(batch_size, len(self.scaled_experiences))
        #  limiting the scaled_experiences list to the memory length
        memory = self.experiences[-self.memory_length:]
        scaled_memory = self.scaled_experiences[-self.memory_length:]

        assert len(memory) == len(scaled_memory
                                  )
        #  indicies for the batch
        indicies = np.random.randint(low=0,
                                     high=len(memory),
                                     size=sample_size)
        #  randomly sample from the memory & returns
        memory_batch = [memory[i] for i in indicies]
        scaled_memory_batch = [scaled_memory[i] for i in indicies]

        observations = np.array([exp.observation for exp in scaled_memory_batch]).reshape(-1, len(self.observation_space))
        actions = np.array([exp.action for exp in memory_batch]).reshape(-1, len(self.action_space))
        returns = np.array([exp.discounted_return for exp in scaled_memory_batch]).reshape(-1, 1)

        assert observations.shape[0] == actions.shape[0]
        assert observations.shape[0] == returns.shape[0]

        return observations, actions, returns
