import asyncio
import edge_tts

segments = [
    "Mom",
    "I got into Renmin University",
    "Mom will definitely find a way",
    "I can only become a big thief",
    "The rest is just a way to wear a mother's hat",
    "Good, whether to take the exam or not",
    "The mode teaches about museums",
    "Mom",
    "I don't want to go to college anymore",
    "Dad, you just completed the drawing",
    "Don't be afraid, child.",
    "Use us.",
    "I said.",
    "The customer service department must be placed in the quick signing."
]

async def test():
    for idx, text in enumerate(segments):
        print(f"Testing segment {idx}: {repr(text)}...")
        try:
            communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
            data = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    data.append(chunk["data"])
            print(f"  Success! Received {len(b''.join(data))} bytes.")
        except Exception as e:
            print(f"  FAILED: {str(e)}")

asyncio.run(test())
