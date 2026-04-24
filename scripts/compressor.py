import sys
import os
from llmlingua import PromptCompressor

# Heuristic: aim to compress to ~30% of original token count, floored at 512, capped at 4096.
# 1 token ≈ 4 chars (rough estimate for English text).
def estimate_target_tokens(text: str) -> int:
    approx_tokens = len(text) // 4
    target = max(512, min(4096, int(approx_tokens * 0.3)))
    return target

def compress_text(content: str):
    compressor = PromptCompressor(
        model_name="microsoft/phi-2",
        device_map="cpu"
    )

    target = estimate_target_tokens(content)

    compressed_result = compressor.compress_prompt(
        content,
        target_token=target,
        instruction="",
        question=""
    )

    print(compressed_result["compressed_prompt"])
    ratio = compressed_result.get("ratio", "unknown")
    print(f"\n\n<!-- ClaudeShrink: compressed {len(content)} chars → target {target} tokens (ratio: {ratio}) -->",
          file=sys.stderr)

def main():
    if len(sys.argv) >= 2:
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found.", file=sys.stderr)
            sys.exit(1)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        # Read from stdin (piped text or prompt)
        if sys.stdin.isatty():
            print("Usage: python compressor.py <filepath>  OR  echo 'text' | python compressor.py", file=sys.stderr)
            sys.exit(1)
        content = sys.stdin.read()

    if not content.strip():
        print("Error: No content to compress.", file=sys.stderr)
        sys.exit(1)

    try:
        compress_text(content)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
