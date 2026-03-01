#!/usr/bin/env python3
"""Test the vision analysis endpoint"""
import httpx
import json
import sys

headers = {
    'Authorization': 'Bearer sk-lm-Y2N47xb4:5WeyyZDm1ulzEXOPjrvc',
    'Content-Type': 'application/json',
}

analysis_prompt = """Analyze this image for language learning.

Instructions:
1. Identify 5 key vocabulary items
2. Provide pronunciation guides
3. Give example sentences in Spanish

Format as JSON:
{
  "analysis": "Brief description",
  "vocabulary": [{"word": "...", "pronunciation": "...", "part_of_speech": "...", "example": "..."}],
  "pronunciation_tips": ["tip1", "tip2"]
}

User Context: test image"""

payload = {
    'model': 'nvidia/nemotron-3-nano',
    'system_prompt': "You are a language learning expert.",
    'input': analysis_prompt,
}

try:
    print("Making request to LMStudio...")
    response = httpx.post(
        'http://127.0.0.1:1234/api/v1/chat',
        json=payload,
        headers=headers,
        timeout=30.0,
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    
    # Extract message
    content = ""
    for output_item in result.get("output", []):
        if output_item.get("type") == "message":
            content = output_item.get("content", "")
            break
    
    print(f"\nResponse length: {len(content)}")
    print(f"First 300 chars:\n{content[:300]}")
    
    # Try JSON parsing
    print("\n--- Attempting JSON parsing ---")
    if "```json" in content:
        json_str = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        json_str = content.split("```")[1].split("```")[0]  
    else:
        json_str = content
    
    print(f"JSON string length: {len(json_str)}")
    parsed = json.loads(json_str.strip())
    print("✓ Parsed successfully!")
    print(f"Keys: {list(parsed.keys())}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
