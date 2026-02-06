from fived.env import Action, FiveDChessEnv


def test_reset_determinism_same_seed():
    env1 = FiveDChessEnv()
    env2 = FiveDChessEnv()
    s1 = env1.reset(seed=42)
    s2 = env2.reset(seed=42)
    assert s1["boards"] == s2["boards"]
    assert s1["timeline_latest"] == s2["timeline_latest"]


def test_reset_seed_variation():
    env = FiveDChessEnv()
    s1 = env.reset(seed=42)
    s2 = env.reset(seed=43)
    assert s1["boards"] != s2["boards"]


def test_has_core_interfaces():
    env = FiveDChessEnv()
    env.reset(seed=42)
    acts = env.legal_actions()
    assert isinstance(acts, list)
    assert isinstance(env.is_terminal(), bool)


def test_step_updates_turn_and_move_count():
    env = FiveDChessEnv()
    env.reset(seed=42)
    action = env.legal_actions()[0]
    _, _, done, _ = env.step(action)
    assert env.move_count == 1
    assert env.side_to_move == "B"
    assert done in (True, False)


def test_illegal_action_rejected():
    env = FiveDChessEnv()
    env.reset(seed=42)
    bad = Action(99, 99, 0, 0, 99, 99, 0, 0)
    try:
        env.step(bad)
        assert False, "Expected ValueError"
    except ValueError:
        assert True


def test_terminal_when_king_missing():
    env = FiveDChessEnv()
    env.reset(seed=42)
    # remove black king from all boards
    for k, board in env.boards.items():
        for r in range(4):
            for c in range(4):
                if board[r][c] == "k":
                    board[r][c] = "."
    assert env.is_terminal()


def test_max_moves_terminal():
    env = FiveDChessEnv(max_moves=1)
    env.reset(seed=42)
    action = env.legal_actions()[0]
    _, _, done, _ = env.step(action)
    assert done


def test_temporal_move_exists_after_progression():
    env = FiveDChessEnv(max_moves=10)
    env.reset(seed=42)
    # Make two spatial moves to create time index > 0 and return white turn.
    env.step(env.legal_actions()[0])
    env.step(env.legal_actions()[0])
    acts = env.legal_actions()
    assert any(a.src_time != a.dst_time for a in acts)


def test_temporal_step_creates_new_timeline():
    env = FiveDChessEnv(max_moves=10)
    env.reset(seed=42)
    env.step(env.legal_actions()[0])
    env.step(env.legal_actions()[0])
    temporal = next(a for a in env.legal_actions() if a.src_time != a.dst_time)
    _, _, _, info = env.step(temporal)
    assert info["temporal"] is True
    assert len(env.timeline_latest) >= 2


def test_reproducibility_50_of_50_fixed_seed_rollouts():
    def rollout_signature(seed: int):
        env = FiveDChessEnv(max_moves=12)
        env.reset(seed=seed)
        sig = []
        while not env.is_terminal():
            acts = env.legal_actions()
            if not acts:
                break
            # deterministic policy: sorted lexicographically, pick first
            acts = sorted(acts, key=lambda a: (a.src_timeline, a.src_time, a.src_row, a.src_col, a.dst_timeline, a.dst_time, a.dst_row, a.dst_col, a.promotion))
            a = acts[0]
            sig.append((a.src_timeline, a.src_time, a.src_row, a.src_col, a.dst_timeline, a.dst_time, a.dst_row, a.dst_col))
            env.step(a)
        return sig

    base = rollout_signature(42)
    for _ in range(50):
        assert rollout_signature(42) == base
