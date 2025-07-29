from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch, os
from huggingface_hub import login

login(token="insert hugging face token here")

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

MODEL = "meta-llama/Llama-2-7b-chat-hf"
bnb_cfg = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model     = AutoModelForCausalLM.from_pretrained(
    MODEL,
    quantization_config=bnb_cfg,
    device_map="auto",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
    trust_remote_code=True
)
model.eval()

SYSTEM_INSTRUCTION = (
    "You are Twit, an insightful, friendly Twitter bot."
    "Answer concisely and factually. Do not use hashtags or emoji and do not reply in quotes."
)

def generate_reply(user_text: str) -> str:
    prompt = f"{SYSTEM_INSTRUCTION}\n\nUser said: “{user_text}”\nBot:"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    out = model.generate(
        **inputs,
        max_new_tokens=60,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id
    )
    text = tokenizer.decode(out[0], skip_special_tokens=True)
    return text.split("Bot:")[-1].strip()
