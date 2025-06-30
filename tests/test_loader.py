from simtest.seeds.loader import load_seed_file, Seed

def test_load_tool_schema_pack():
    seeds = load_seed_file("seeds/tool-schema-sanity.yaml")

    assert isinstance(seeds, list)
    assert all(isinstance(s, Seed) for s in seeds)
    assert len(seeds) >= 3  # We added 3
