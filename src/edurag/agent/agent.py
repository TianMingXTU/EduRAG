import asyncio
import argparse
from edurag.agent.orchestrator import run_agent


async def main():
    parser = argparse.ArgumentParser(description="EduRAG - CLI")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--query", "-q", type=str, help="Single query and exit")
    group.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive session"
    )
    args = parser.parse_args()

    if args.query:
        result = await run_agent(args.query)
        print(f"\nAnswer: {result['answer']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Sources: {result['sources']}")

    elif args.interactive:
        print("EduRAG interactive mode. Type 'exit' to quit.")
        while True:
            q = input("\n>> ").strip()
            if q.lower() in ("exit", "quit"):
                break
            result = await run_agent(q)
            print(f"\n{result['answer']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
