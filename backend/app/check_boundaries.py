"""Fail CI if deterministic stages import the LLM package."""
from pathlib import Path
FORBIDDEN=('entity_resolution','contradiction','validation')
def test_boundaries():
    root=Path(__file__).parent/'pipeline'; violations=[]
    for name in FORBIDDEN:
        for path in (root/name).rglob('*.py'):
            if 'app.llm' in path.read_text(): violations.append(str(path))
    assert not violations, f'LLM import boundary violated: {violations}'
if __name__=='__main__': test_boundaries()
