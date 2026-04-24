import sys
import os
import argparse
from llmlingua import PromptCompressor


def _patch_get_ppl(compressor_instance):
    """Monkey-patch get_ppl to handle transformers 5.x DynamicCache format."""
    if not hasattr(compressor_instance.__class__, 'get_ppl'):
        return
    import torch
    original_get_ppl = compressor_instance.__class__.get_ppl

    def _get_ppl(self, text, granularity="sentence", input_ids=None, attention_mask=None,
                 past_key_values=None, return_kv=False, end=None,
                 condition_mode="none", condition_pos_id=0):
        if input_ids is None:
            tokenized_text = self.tokenizer(text, return_tensors="pt")
            input_ids = tokenized_text["input_ids"].to(self.device)
            attention_mask = tokenized_text["attention_mask"].to(self.device)

        if past_key_values is not None:
            if isinstance(past_key_values, (list, tuple)):
                past_length = past_key_values[0][0].shape[2]
                dc = getattr(self, '_cached_dynamic_cache', None)
                if dc is not None:
                    for i, (k, v) in enumerate(past_key_values):
                        dc.layers[i].keys = k
                        dc.layers[i].values = v
                    past_key_values = dc
            else:
                past_length = past_key_values.get_seq_length()
        else:
            past_length = 0

        if end is None:
            end = input_ids.shape[1]
        end = min(end, past_length + self.max_position_embeddings)

        with torch.no_grad():
            response = self.model(
                input_ids[:, past_length:end],
                attention_mask=attention_mask[:, :end],
                past_key_values=past_key_values,
                use_cache=True,
            )
            pkv = response.past_key_values
            if hasattr(pkv, 'layers'):
                self._cached_dynamic_cache = pkv
                past_key_values = [[layer.keys, layer.values] for layer in pkv.layers]
            else:
                past_key_values = pkv

        shift_logits = response.logits[..., :-1, :].contiguous()
        shift_labels = input_ids[..., past_length + 1:end].contiguous()
        active = (attention_mask[:, past_length:end] == 1)[..., :-1].view(-1)
        active_logits = shift_logits.view(-1, shift_logits.size(-1))[active]
        active_labels = shift_labels.view(-1)[active]
        loss_fct = torch.nn.CrossEntropyLoss(reduction="none")
        loss = loss_fct(active_logits, active_labels)
        if condition_mode == "before":
            loss = loss[:condition_pos_id]
        elif condition_mode == "after":
            loss = loss[condition_pos_id:]
        res = loss.mean() if granularity == "sentence" else loss
        return (res, past_key_values) if return_kv else res

    import types
    compressor_instance.get_ppl = types.MethodType(_get_ppl, compressor_instance)


# 1 token ≈ 4 chars (rough estimate for English text).
def estimate_target_tokens(text: str) -> int:
    approx_tokens = len(text) // 4
    return max(512, min(4096, int(approx_tokens * 0.3)))


def compress_text(content: str, question: str = "", instruction: str = ""):
    approx_tokens = len(content) // 4

    # Input is already small — no benefit from compressing
    if approx_tokens <= 512:
        print(content)
        print(f"<!-- ClaudeShrink: input ~{approx_tokens} tokens, skipped compression -->", file=sys.stderr)
        return

    target = estimate_target_tokens(content)

    compressor = PromptCompressor(model_name="gpt2", device_map="cpu")
    _patch_get_ppl(compressor)

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
            instruction=instruction,
            question=question,
            target_token=per_chunk_target
        )
        compressed_chunks.append(res["compressed_prompt"])

    final_compressed = "\n".join(compressed_chunks)
    print(final_compressed)

    hint = f" | question='{question}'" if question else ""
    hint += f" | instruction='{instruction}'" if instruction else ""
    print(f"\n\n<!-- ClaudeShrink: compressed {len(content)} chars in {len(chunks)} chunks → ~target {target} tokens{hint} -->",
          file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="ClaudeShrink: compress large text with LLMLingua")
    parser.add_argument("file", nargs="?", help="Path to input file (omit to read from stdin)")
    parser.add_argument("--question", "-q", default="", help="Question or intent — biases compression to keep relevant content")
    parser.add_argument("--instruction", "-i", default="", help="Instruction hint — additional context for what matters")
    args = parser.parse_args()

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        if sys.stdin.isatty():
            print("Usage: python compressor.py <filepath> [--question Q] [--instruction I]", file=sys.stderr)
            sys.exit(1)
        content = sys.stdin.read()

    if not content.strip():
        print("Error: No content to compress.", file=sys.stderr)
        sys.exit(1)

    try:
        compress_text(content, question=args.question, instruction=args.instruction)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
