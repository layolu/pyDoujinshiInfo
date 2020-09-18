from typing import Dict, List

def taglist_to_dict(taglist: List[str]) -> Dict[int, str]:
    return {'tags[{}]'.format(i): v for i, v in enumerate(taglist)}