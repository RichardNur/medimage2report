
import os, torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# point to your local snapshot
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_QWEN_LOCAL = os.path.join(BASE_DIR, "data", "models", "Qwen2.5-1.5B")


# pick MPS if you’re on Apple Silicon, else CPU
device = "mps" if torch.backends.mps.is_available() else "cpu"

# load tokenizer & model, purely local
tokenizer_qwen = AutoTokenizer.from_pretrained(
    _QWEN_LOCAL,
    trust_remote_code=True,
    local_files_only=True,
)

model_qwen = AutoModelForCausalLM.from_pretrained(
    _QWEN_LOCAL,
    trust_remote_code=True,
    local_files_only=True,
    torch_dtype=torch.float16,
    device_map="auto",
    low_cpu_mem_usage=True,
)



def call_qwen(prompt: str) -> str:
    # tokenize + send to device
    inputs   = tokenizer_qwen(prompt, return_tensors="pt").to(device)
    input_ids = inputs["input_ids"]
    input_len = input_ids.shape[1]

    # generate
    outputs  = model_qwen.generate(
        **inputs,
        max_new_tokens=512,
        eos_token_id=tokenizer_qwen.eos_token_id,
        pad_token_id=tokenizer_qwen.eos_token_id,
        no_repeat_ngram_size=3,           # reduce simple repetition
        repetition_penalty=1.2,           # discourage repeats
    )

    # slice out only the newly generated tokens
    gen_ids  = outputs[0][input_len:]
    result   = tokenizer_qwen.decode(gen_ids, skip_special_tokens=True)
    print(type(result))
    print("Result: ", result)
    return result.strip()