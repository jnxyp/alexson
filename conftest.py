import sys
from pathlib import Path

# 将 alexson 的父目录加入 sys.path，使 `import alexson` 可用
sys.path.insert(0, str(Path(__file__).parent.parent))
