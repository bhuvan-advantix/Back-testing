import google.generativeai as genai

API_KEY = "AIzaSyBuvQm-gVhwAeiwyx83w3xIEO_8d8iZbEw"

print("Testing gemini-2.5-flash (you have 20 requests/day quota)...")
print("="*60)

genai.configure(api_key=API_KEY)

try:
    # Use gemini-2.5-flash (your dashboard shows you have quota!)
    print("\nTrying gemini-2.5-flash...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Say hello in 3 words")
    
    print("✅ SUCCESS! Gemini is working!")
    print(f"Response: {response.text}")
    print("\n" + "="*60)
    print("GEMINI API IS NOW WORKING!")
    print("="*60)
    print("Model: gemini-2.5-flash")
    print("Free Quota: 20 requests/day, 5 requests/minute")
    print("\nUpdate your config_real.py:")
    print("GEMINI_CONFIG = {")
    print("    'api_key': 'AIzaSyBuvQm-gVhwAeiwyx83w3xIEO_8d8iZbEw',")
    print("    'model': 'gemini-2.5-flash',")
    print("}")
    
except Exception as e:
    error_str = str(e)
    print(f"❌ FAILED: {error_str[:300]}")
    
    if "429" in error_str:
        print("\nYou've used up today's 20 requests.")
        print("Wait until midnight UTC for quota reset.")
    elif "404" in error_str:
        print("\nModel not found. Check model name.")
    else:
        print("\nUnexpected error. Check API key and billing.")

print("\n" + "="*60)