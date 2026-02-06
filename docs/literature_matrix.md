# Literature Matrix (Item 003)

| Work | Search Strategy | Representation | Training Regime | Strength Metric |
|---|---|---|---|---|
| AlphaGo (2016) | MCTS + policy/value | board planes | SL + RL + self-play | 99.8% vs Fan Hui |
| AlphaGo Zero (2017) | PUCT MCTS | raw planes | pure self-play | 100-0 vs AlphaGo Lee |
| AlphaZero (2018) | PUCT MCTS | board tensor | self-play multi-game | superhuman match results |
| MuZero (2020) | latent MCTS | learned dynamics latent | self-play + model learning | SOTA board/Atari |
| EfficientZero (2021) | sample-efficient MCTS | latent | model-based RL | Atari data-efficiency |
| Gumbel MuZero (2021) | gumbelized policy improvement | latent | self-play | planning gains |
| Leela Chess Zero | PUCT | 112-plane chess tensor | distributed self-play | chess Elo |
| KataGo | MCTS with score utility | Go features | self-play + aux targets | top Go Elo |
| ELF OpenGo | MCTS | Go tensor | reproducible self-play | pro-level strength |
| Polygames | AlphaZero-style MCTS | game tensor | self-play | internal Elo |
| Sampled MuZero | sampled planning | latent | model-based RL | large-action gains |
| Stochastic MuZero | stochastic tree search | latent chance nodes | model-based RL | stochastic control gains |
| DreamerV3 | imagined rollouts | RSSM latent | world-model RL | broad benchmark wins |
| Muesli | policy/value regularized planning | conv features | off-policy RL | Atari scores |
| OpenSpiel AlphaZero | MCTS | game tensors | self-play | benchmark win rates |
| MiniZero | AlphaZero/MuZero | board+latent | self-play | Elo progression |
| DeepNash | population planning | strategic features | population RL | Diplomacy rank |
| Stockfish NNUE | alpha-beta + NN eval | NNUE sparse | supervised + search | top chess Elo |
| LCZero transformer era | PUCT | transformer planes | self-play | TCEC/CCRL strength |
| MuZero Unplugged | offline planning | latent | offline RL | offline benchmark metrics |
