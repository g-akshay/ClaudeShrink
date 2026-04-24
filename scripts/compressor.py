import sys
import os
from llmlingua import PromptCompressor

# 1 token ≈ 4 chars (rough estimate for English text).
def estimate_target_tokens(text: str) -> int:
    approx_tokens = len(text) // 4
    target = max(512, min(4096, int(approx_tokens * 0.3)))
    return target, approx_tokens

def compress_text(content: str):
    target, approx_tokens = estimate_target_tokens(content)

    # Input is already small — no benefit from compressing
    if approx_tokens <= 512:
        print(content)
        print(f"<!-- ClaudeShrink: input ~{approx_tokens} tokens, skipped compression -->", file=sys.stderr)
        return

    # Using gpt2 fixes the unpack error and runs much faster on CPU
    compressor = PromptCompressor(
        model_name="gpt2",
        device_map="cpu"
    )

    # Split text into manageable chunks to stay under GPT2's 1024-token limit
    lines = content.split('\n')
    chunks = []
    current_chunk = ""

    for line in lines:
        # 1500 characters is safely under the GPT2 token limit (1024)
        if len(current_chunk) + len(line) > 1500:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += ("\n" + line if current_chunk else line)

    if current_chunk:
        chunks.append(current_chunk)

    compressed_chunks = []
    per_chunk_target = max(128, target // len(chunks)) if chunks else target
    
    for c in chunks:
        res = compressor.compress_prompt(
            context=[c],
            instruction="",
            question="",
            target_token=per_chunk_target
        )
        compressed_chunks.append(res["compressed_prompt"])

    final_compressed = "\n".join(compressed_chunks)
    print(final_compressed)
    
    print(f"\n\n<!-- ClaudeShrink: compressed {len(content)} chars in {len(chunks)} chunks → ~target {target} tokens -->",
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
