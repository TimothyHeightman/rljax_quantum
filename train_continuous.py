import argparse
import os
from datetime import datetime

import gym

from rljax import CONTINUOUS_ALGOS
from rljax.common.trainer import Trainer


def run(args):
    env = gym.make(args.env_id)
    env_test = gym.make(args.env_id)

    algo = CONTINUOUS_ALGOS[args.algo](
        state_space=env.observation_space,
        action_space=env.action_space,
        seed=args.seed,
    )

    time = datetime.now().strftime("%Y%m%d-%H%M")
    log_dir = os.path.join("logs", args.env_id, args.algo, f"seed{args.seed}-{time}")

    trainer = Trainer(
        env=env,
        env_test=env_test,
        algo=algo,
        log_dir=log_dir,
        num_steps=args.num_steps,
        eval_interval=args.eval_interval,
        seed=args.seed,
    )
    trainer.train()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--algo", type=str, default="sac")
    p.add_argument("--num_steps", type=int, default=50000)
    p.add_argument("--eval_interval", type=int, default=1000)
    p.add_argument("--env_id", type=str, default="InvertedPendulum-v2")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()
    run(args)