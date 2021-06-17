from retro_data_structures.ancs import ANCS


def test_compare_p1(prime1_pwe_project):
    input_path = prime1_pwe_project.joinpath("Resources/Uncategorized/alpha_metaree.ANCS")
    game = 1
    raw = input_path.read_bytes()

    data = ANCS.parse(raw, target_game=game)
    encoded = ANCS.build(data, target_game=game)

    assert encoded == raw


def test_compare_p2(prime2_pwe_project):
    input_path = prime2_pwe_project.joinpath("Resources/Uncategorized/annihilatorBeam.ANCS")
    game = 2
    raw = input_path.read_bytes()

    data = ANCS.parse(raw, target_game=game)
    encoded = ANCS.build(data, target_game=game)

    assert encoded == raw