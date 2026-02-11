"""
Print the final prompt (system + context + history + query) before LLM call.
Uses the same RAGEngine functions as the app.
"""
import argparse
from core.rag_engine import rag_engine

# Hard-coded chat ID for prompt inspection
HARDCODED_CHAT_ID = "10fc0bb0-3bd1-4967-8294-592b174485d4"


def render_messages(messages):
    parts = []
    for msg in messages:
        role = getattr(msg, "type", None) or getattr(msg, "role", None) or "unknown"
        content = getattr(msg, "content", "")
        parts.append(f"[{role}]\n{content}")
    return "\n\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Show final prompt sent to the LLM")
    parser.add_argument("query", nargs="?", help="User query")
    parser.add_argument("--chat-id", dest="chat_id", default=None, help="Chat ID for history (ignored; using hard-coded ID)")
    args = parser.parse_args()

    query = args.query
    if not query:
        query = input("Enter query: ").strip()
        if not query:
            print("No query provided.")
            return

    chat_id = HARDCODED_CHAT_ID
    context, history, standalone_query = rag_engine._get_context_and_history(query, chat_id)

    chain_input = {
        "context": context,
        "history": history,
        "input": standalone_query,
    }

    messages = rag_engine.prompt_template.format_messages(**chain_input)
    print(render_messages(messages))


if __name__ == "__main__":
    main()
