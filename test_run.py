from deepseek_wrapper import DeepSeekClient, DeepSeekConfig
import asyncio

# 1. Completions endpoint (requires beta base_url)
completions_client = DeepSeekClient(config=DeepSeekConfig(base_url="https://api.deepseek.com/beta"))
print("Sync result (completions, beta API):")
try:
    result = completions_client.generate_text("Hello, DeepSeek!", max_tokens=32)
    print(result)
except Exception as e:
    print(f"Sync error: {e}")

print("\nAsync result (completions, beta API):")
async def main():
    try:
        result = await completions_client.async_generate_text("Hello, DeepSeek async!", max_tokens=32)
        print(result)
    except Exception as e:
        print(f"Async error: {e}")
asyncio.run(main())

# 2. Chat completion endpoint (works on main API)
chat_client = DeepSeekClient()
print("\nSync result (chat completion, main API):")
try:
    chat_result = chat_client.chat_completion([
        {"role": "user", "content": "Hello, DeepSeek!"}
    ])
    print(chat_result)
except Exception as e:
    print(f"Chat sync error: {e}")

print("\nAsync result (chat completion, main API):")
async def chat_main():
    try:
        chat_result = await chat_client.async_chat_completion([
            {"role": "user", "content": "Hello, DeepSeek async!"}
        ])
        print(chat_result)
    except Exception as e:
        print(f"Chat async error: {e}")
asyncio.run(chat_main()) 