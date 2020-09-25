import numpy as np
from gym.spaces import Box, Discrete

import jax


class ReplayBuffer:
    """
    Replay Buffer.
    """

    def __init__(self, buffer_size, state_space, action_space):
        self._n = 0
        self._p = 0
        self.buffer_size = buffer_size

        self.state = np.empty((buffer_size, *state_space.shape), dtype=np.float32)
        self.reward = np.empty((buffer_size, 1), dtype=np.float32)
        self.done = np.empty((buffer_size, 1), dtype=np.float32)
        self.next_state = np.empty((buffer_size, *state_space.shape), dtype=np.float32)

        if type(action_space) == Box:
            self.action = np.empty((buffer_size, *action_space.shape), dtype=np.float32)
        elif type(action_space) == Discrete:
            self.action = np.empty((buffer_size, 1), dtype=np.int64)
        else:
            NotImplementedError

    def append(self, state, action, reward, done, next_state):
        self.state[self._p] = state
        self.action[self._p] = action
        self.reward[self._p] = float(reward)
        self.done[self._p] = float(done)
        self.next_state[self._p] = next_state

        self._p = (self._p + 1) % self.buffer_size
        self._n = min(self._n + 1, self.buffer_size)

    def sample(self, batch_size):
        idxes = np.random.randint(low=0, high=self._n, size=batch_size)
        return (
            jax.device_put(self.state[idxes]),
            jax.device_put(self.action[idxes]),
            jax.device_put(self.reward[idxes]),
            jax.device_put(self.done[idxes]),
            jax.device_put(self.next_state[idxes]),
        )
