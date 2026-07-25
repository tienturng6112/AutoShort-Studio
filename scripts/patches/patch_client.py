with open('backend/providers/speech/gemini/client.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_models_logic = '''                    is_audio = "1.5" in m.get("name", "") and ("flash" in m.get("name", "") or "pro" in m.get("name", ""))
                    models.append(GeminiModelInfo(
                        name=m["name"].replace("models/", ""),
                        display_name=m.get("displayName", m["name"]),
                        supports_audio=is_audio
                    ))'''

new_models_logic = '''                    name = m.get("name", "").replace("models/", "")
                    display = m.get("displayName", name)
                    methods = m.get("supportedGenerationMethods", [])
                    
                    caps = ["Chat", "Translation"]
                    is_audio = "1.5" in name and ("flash" in name or "pro" in name)
                    if is_audio:
                        caps.append("Speech")
                    if "1.5" in name or "vision" in name:
                        caps.append("Image")
                    if "streamGenerateContent" in methods:
                        caps.append("Streaming")
                    if "thinking" in name or "pro" in name:
                        caps.append("Thinking")
                        
                    models.append(GeminiModelInfo(
                        name=name,
                        display_name=display,
                        supports_audio=is_audio,
                        capabilities=caps
                    ))'''

text = text.replace(old_models_logic, new_models_logic)

with open('backend/providers/speech/gemini/client.py', 'w', encoding='utf-8') as f:
    f.write(text)
