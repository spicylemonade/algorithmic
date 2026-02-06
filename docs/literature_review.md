# Literature Review: AlphaGo-Style and Large-Action-Space Game Agents

1. **Kocsis and Szepesvari (2006) - Bandit Based Monte-Carlo Planning**
   - Introduces UCT and the exploration-exploitation rule that underpins modern tree search. It formalizes how simulation statistics can guide planning with finite samples. This is a direct base for PUCT-style 5D search.

2. **Coulom (2006) - Efficient Selectivity and Backup Operators in Monte-Carlo Tree Search**
   - Presents practical backup/selectivity improvements in early MCTS engines. It emphasizes that search control policy strongly affects strength. This is relevant when timeline branches inflate action space.

3. **Browne et al. (2012) - A Survey of Monte Carlo Tree Search Methods**
   - Consolidates key MCTS variants and engineering techniques (RAVE, progressive widening, transpositions). It is a useful design map for adapting MCTS to non-standard domains. 5D chess likely needs several of these extensions simultaneously.

4. **Silver et al. (2016, Nature) - Mastering the game of Go with deep neural networks and tree search**
   - Combines policy/value networks with MCTS to reduce effective branching. It demonstrates large gains from learned priors plus value backups. This is the canonical AlphaGo pattern.

5. **Silver et al. (2017, Nature) - Mastering the game of Go without human knowledge**
   - Establishes pure self-play as sufficient for superhuman policy improvement. It simplifies the training loop and improves final strength. This motivates avoiding handcrafted opening data.

6. **Silver et al. (2018, Science) - A general reinforcement learning algorithm that masters chess, shogi, and Go**
   - Shows one rules-only method can span multiple board games. It validates robustness of PUCT + residual policy-value networks. This cross-game transferability is encouraging for 5D chess.

7. **Schrittwieser et al. (2020, Nature) - MuZero**
   - Learns latent dynamics and performs planning without explicit game rules in the model. It suggests strong play can emerge from compact internal transition models. This may cut simulation costs for timeline dynamics.

8. **Hubert et al. (2021) - Learning and Planning in Complex Action Spaces (Gumbel MuZero)**
   - Uses Gumbel-based policy improvement to produce better search targets under finite simulations. It improves policy learning stability and efficiency. This is promising where per-move search budget is tight.

9. **Ye et al. (2021) - Mastering Complex Control in MOBA Games with Deep RL**
   - Demonstrates scalable self-play and population-style training in enormous action spaces. While not board-game specific, it provides robust curriculum and exploit-loop mitigation lessons. These are relevant to 5D self-play stability.

10. **Vinyals et al. (2019, Nature) - Grandmaster level in StarCraft II using multi-agent RL (AlphaStar)**
   - Introduces league-based training to improve robustness against non-transitive strategies. It shows diversity mechanisms reduce overfitting to one policy family. Similar ideas can harden 5D agents.

11. **Tian et al. (2019) - ELF OpenGo: An Analysis and Open Reimplementation of AlphaZero**
   - Provides reproducibility insights and practical training details for AlphaZero-like systems. It documents sensitivity to optimization and data generation throughput. This is valuable for engineering realistic training loops.

12. **Wu (2019) - Accelerating Self-Play Learning in Go (KataGo)**
   - Adds efficiency and target-shaping methods that improve sample efficiency in self-play. It highlights benefit of richer targets and careful replay policies. Many of these ideas are transferable beyond Go.

13. **Campbell, Hoane, Hsu (2002) - Deep Blue**
   - Represents high-performance classical search with expert heuristics and hardware-aware optimization. It shows tactical strength can come from engineering throughput and pruning quality. This informs non-learning baselines and benchmarking.

14. **Vaswani et al. (2017) - Attention Is All You Need**
   - Introduces transformer attention with strong long-range dependency modeling. For board games, attention can represent non-local interactions more directly than local convolutions. This is relevant for cross-timeline dependencies.

15. **Chen et al. (2021) - Decision Transformer**
   - Recasts RL as sequence modeling with transformers, conditioning on desired return. It shows competitive control performance without explicit Bellman backups. This offers an alternative policy-learning view for search-distilled trajectories.

16. **Janner et al. (2021) - Trajectory Transformer**
   - Models trajectories autoregressively and uses planning in model space. It provides a transformer-compatible route to planning over latent sequence dynamics. This informs potential hybrid planning architectures for 5D chess.

17. **Reed et al. (2022) - A Generalist Agent (Gato)**
   - Demonstrates a single transformer trained on diverse tasks can act across modalities and domains. It supports the idea that unified sequence models can represent broad control skills. For 5D chess, it motivates shared tokenization across timelines.

18. **Schadd, Winands, Uiterwijk, van den Herik (2012) - Single-Player MCTS and Chess Variants**
   - Explores MCTS behavior and limitations in chess-like tactical settings. It reinforces that priors and rollout design are critical outside Go. This aligns with expected 5D search challenges.
