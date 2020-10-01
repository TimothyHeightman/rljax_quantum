import math

import haiku as hk
import jax.numpy as jnp
from jax import nn

from rljax.network.base import MLP, DQNBody


class ContinuousVFunction(hk.Module):
    """
    Critic for PPO.
    """

    def __init__(
        self,
        num_critics=1,
        hidden_units=(64, 64),
        hidden_activation=jnp.tanh,
    ):
        super(ContinuousVFunction, self).__init__()
        self.num_critics = num_critics
        self.hidden_units = hidden_units
        self.hidden_activation = hidden_activation

    def __call__(self, x):
        def _fn(x):
            return MLP(1, self.hidden_units, self.hidden_activation)(x)

        if self.num_critics == 1:
            return _fn(x)
        return [_fn(x) for _ in range(self.num_critics)]


class ContinuousQFunction(hk.Module):
    """
    Critic for DDPG, TD3 and SAC.
    """

    def __init__(
        self,
        num_critics=2,
        hidden_units=(400, 300),
        hidden_activation=nn.relu,
    ):
        super(ContinuousQFunction, self).__init__()
        self.num_critics = num_critics
        self.hidden_units = hidden_units
        self.hidden_activation = hidden_activation

    def __call__(self, s, a):
        def _fn(x):
            return MLP(1, self.hidden_units, self.hidden_activation)(x)

        x = jnp.concatenate([s, a], axis=1)
        if self.num_critics == 1:
            return _fn(x)
        return [_fn(x) for _ in range(self.num_critics)]


class DiscreteQFunction(hk.Module):
    """
    Critic for DQN and SAC-Discrete.
    """

    def __init__(
        self,
        action_space,
        num_critics=1,
        hidden_units=(512,),
        dueling_net=True,
        hidden_activation=nn.relu,
    ):
        super(DiscreteQFunction, self).__init__()
        self.action_space = action_space
        self.num_critics = num_critics
        self.hidden_units = hidden_units
        self.dueling_net = dueling_net
        self.hidden_activation = hidden_activation

    def __call__(self, x):
        def _fn(x):
            if len(x.shape) == 4:
                x = DQNBody()(x)
            output = MLP(self.action_space.n, self.hidden_units, self.hidden_activation)(x)
            if self.dueling_net:
                baseline = MLP(1, self.hidden_units, self.hidden_activation)(x)
                return output + baseline - output.mean(axis=1, keepdims=True)
            else:
                return output

        if self.num_critics == 1:
            return _fn(x)
        return [_fn(x) for _ in range(self.num_critics)]


class DiscreteQuantileFunction(hk.Module):
    """
    Critic for QR-DQN.
    """

    def __init__(
        self,
        action_space,
        num_critics=1,
        num_quantiles=200,
        hidden_units=(512,),
        dueling_net=True,
        hidden_activation=nn.relu,
    ):
        super(DiscreteQuantileFunction, self).__init__()
        self.action_space = action_space
        self.num_critics = num_critics
        self.num_quantiles = num_quantiles
        self.hidden_units = hidden_units
        self.dueling_net = dueling_net
        self.hidden_activation = hidden_activation

    def __call__(self, x):
        def _fn(x):
            if len(x.shape) == 4:
                x = DQNBody()(x)
            output = MLP(self.action_space.n * self.num_quantiles, self.hidden_units, self.hidden_activation)(x)
            output = output.reshape(-1, self.num_quantiles, self.action_space.n)
            if self.dueling_net:
                baseline = MLP(self.num_quantiles, self.hidden_units, self.hidden_activation)(x)
                baseline = baseline.reshape(-1, self.num_quantiles, 1)
                return output + baseline - output.mean(axis=2, keepdims=True)
            else:
                return output

        if self.num_critics == 1:
            return _fn(x)
        return [_fn(x) for _ in range(self.num_critics)]


class DiscreteImplicitQuantileFunction(hk.Module):
    """
    Critic for IQN.
    """

    def __init__(
        self,
        action_space,
        num_critics=1,
        num_quantiles=64,
        num_cosines=64,
        hidden_units=(512,),
        dueling_net=True,
        hidden_activation=nn.relu,
    ):
        super(DiscreteImplicitQuantileFunction, self).__init__()
        self.action_space = action_space
        self.num_critics = num_critics
        self.num_quantiles = num_quantiles
        self.num_cosines = num_cosines
        self.hidden_units = hidden_units
        self.hidden_activation = hidden_activation
        self.dueling_net = dueling_net
        self.pi = math.pi * jnp.arange(1, num_cosines + 1, dtype=jnp.float32).reshape(1, 1, num_cosines)

    def __call__(self, x, tau):
        def _fn(x, tau):
            if len(x.shape) == 4:
                x = DQNBody()(x)
            # Calculate features.
            feature_dim = x.shape[1]
            cosine = jnp.cos(jnp.expand_dims(tau, 2) * self.pi).reshape(-1, self.num_cosines)
            cosine_feature = nn.relu(hk.Linear(feature_dim)(cosine)).reshape(-1, self.num_quantiles, feature_dim)
            x = (x.reshape(-1, 1, feature_dim) * cosine_feature).reshape(-1, feature_dim)
            # Apply quantile network.
            output = MLP(self.action_space.n, self.hidden_units, self.hidden_activation)(x)
            output = output.reshape(-1, self.num_quantiles, self.action_space.n)
            if self.dueling_net:
                baseline = MLP(1, self.hidden_units, self.hidden_activation)(x)
                baseline = baseline.reshape(-1, self.num_quantiles, 1)
                return output + baseline - output.mean(axis=2, keepdims=True)
            else:
                return output

        if self.num_critics == 1:
            return _fn(x, tau)
        return [_fn(x, tau) for _ in range(self.num_critics)]
