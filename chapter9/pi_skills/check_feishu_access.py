"""复用飞书 CLI 的只读授权检查。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chapter9.cli_skills.check_feishu_access import main
if __name__ == "__main__":
    main()
