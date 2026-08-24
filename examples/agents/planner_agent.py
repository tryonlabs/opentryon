from dotenv import load_dotenv

load_dotenv()

import argparse
import json
from pathlib import Path

from tryon.agents.planner import PlannerAgent


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Planner Agent — classify a request and delegate to fashion / model_swap / vton.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python planner_agent.py --prompt "Generate a red evening gown on a runway" --dry-run
  python planner_agent.py --prompt "Try this shirt on the model" --person person.jpg --garment shirt.jpg
  python planner_agent.py --prompt "Replace with a 30s athletic model" --image outfit.jpg
        """,
    )
    parser.add_argument("--prompt", required=True, help="Natural-language request")
    parser.add_argument("--person", default=None, help="Person / model image (VTON)")
    parser.add_argument("--garment", default=None, help="Garment image (VTON)")
    parser.add_argument("-i", "--image", default=None, help="Reference image (model swap / fashion)")
    parser.add_argument("--dry-run", action="store_true", help="Classify only; do not run the specialist")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("-o", "--output", default=None, help="Write the JSON result to this path")
    args = parser.parse_args()

    agent = PlannerAgent()
    result = agent.run(
        args.prompt,
        person_image=args.person,
        garment_image=args.garment,
        image=args.image,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
    print(json.dumps({k: v for k, v in result.items() if k != "specialist"}, indent=2, default=str))
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, default=str))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
