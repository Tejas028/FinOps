from normalization.tag_parser import TagParser

def test_standard_environment_extraction():
    parser = TagParser()
    tags_dict, env, team = parser.parse('{"environment": "production", "team": "data-engineering"}')
    assert env == "prod"
    assert team == "data-engineering"

def test_alias_key_extraction():
    parser = TagParser()
    tags_dict, env, team = parser.parse('{"env": "staging", "owner": "platform"}')
    assert env == "staging"
    assert team == "platform"

def test_unknown_environment_value():
    parser = TagParser()
    tags_dict, env, team = parser.parse('{"environment": "canary"}')
    assert env == "canary"

def test_no_env_team_keys():
    parser = TagParser()
    tags_dict, env, team = parser.parse('{"region": "us-east-1", "cost_center": "1234"}')
    assert env is None
    assert team == "1234"

def test_malformed_json():
    parser = TagParser()
    tags_dict, env, team = parser.parse('{"broken json')
    assert tags_dict == {}
    assert env is None
    assert team is None
