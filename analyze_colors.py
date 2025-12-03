from PIL import Image
from collections import Counter

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def analyze_image(path):
    try:
        img = Image.open(path)
        img = img.convert('RGB')
        # Resize to speed up processing and ignore small noise
        img = img.resize((150, 150))
        pixels = list(img.getdata())
        
        # Simple heuristic: ignore pure white/black if they are backgrounds
        # But for now, let's just show the top 5 distinct colors
        counts = Counter(pixels)
        common = counts.most_common(10)
        
        print(f"--- Analysis for {path} ---")
        for color, count in common:
            hex_val = rgb_to_hex(color)
            print(f"Hex: {hex_val} | RGB: {color} | Count: {count}")
            
    except Exception as e:
        print(f"Error analyzing image: {e}")

if __name__ == "__main__":
    analyze_image("logo.jpg")



