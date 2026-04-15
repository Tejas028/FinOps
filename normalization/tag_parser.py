import json
from typing import Tuple, Optional, Dict

class TagParser:
    # Keys to check for environment extraction (priority order)
    ENV_KEYS = ["environment", "env", "stage", "tier"]
    ENV_VALUES = {
        "prod": "prod", "production": "prod",
        "staging": "staging", "stage": "staging", "stg": "staging",
        "dev": "dev", "development": "dev",
        "test": "test", "testing": "test", "qa": "test",
    }

    # Keys to check for team extraction (priority order)
    TEAM_KEYS = ["team", "owner", "squad", "department", "cost_center", "project", "app"]

    def parse(self, tags_str: str) -> Tuple[dict, Optional[str], Optional[str]]:
        """
        1. json.loads(tags_str) → dict (handle malformed JSON → return {})
        2. Extract environment:
           - Iterate ENV_KEYS in priority order
           - If key found in tags, normalize value using ENV_VALUES map
           - If value not in ENV_VALUES → return as-is (lowercased)
           - If no key found → return None
        3. Extract team:
           - Iterate TEAM_KEYS in priority order
           - Return first non-empty string value found
           - If none found → return None
        4. Return (tags_dict, environment, team)
        """
        tags_dict = {}
        if tags_str:
            try:
                parsed = json.loads(tags_str)
                if isinstance(parsed, dict):
                    tags_dict = parsed
            except json.JSONDecodeError:
                pass

        environment = None
        for key in self.ENV_KEYS:
            if key in tags_dict:
                val = str(tags_dict[key]).lower()
                environment = self.ENV_VALUES.get(val, val)
                break

        team = None
        for key in self.TEAM_KEYS:
            if key in tags_dict and tags_dict[key]:
                team = str(tags_dict[key])
                break

        return tags_dict, environment, team
