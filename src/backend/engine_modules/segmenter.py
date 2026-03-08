import re

class TextSegmenter:
    @staticmethod
    def segment_text(text: str) -> list[str]:
        # 1. First split by major punctuation to create sentences
        initial_chunks = re.split(r'([.!?。！？\n\r]+)', text)
        sentences = []
        for i in range(0, len(initial_chunks)-1, 2):
            s = initial_chunks[i] + initial_chunks[i+1]
            if s.strip(): sentences.append(s.strip())
        if len(initial_chunks) % 2 == 1 and initial_chunks[-1].strip():
            sentences.append(initial_chunks[-1].strip())
            
        # 2. Recursive split for long sentences (> 150 chars) to prevent drift
        final_chunks = []
        for s in sentences:
            if len(s) > 150:
                # Try to split by commas or semi-colons
                sub = re.split(r'([,;，；])', s)
                current = ""
                for part in sub:
                    if len(current) + len(part) < 150:
                        current += part
                    else:
                        if current: final_chunks.append(current.strip())
                        current = part
                if current: final_chunks.append(current.strip())
            else:
                final_chunks.append(s)

        if not final_chunks: final_chunks = [text]
        return final_chunks
