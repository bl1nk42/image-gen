#!/usr/bin/env python3
"""
Test script for Image Generation Microservice
"""

import requests
import json
import time
import sys
from datetime import datetime


def test_health_endpoint(base_url):
    """Test the health check endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed: {data}")
                return False
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed with error: {e}")
        return False


def test_image_generation_endpoint(base_url):
    """Test the image generation endpoint"""
    print("Testing image generation endpoint...")
    
    test_cases = [
        {
            "name": "Basic prompt",
            "data": {
                "prompt": "A beautiful sunset over mountains"
            }
        },
        {
            "name": "With style",
            "data": {
                "prompt": "A cat sitting on a windowsill",
                "style": "photorealistic"
            }
        },
        {
            "name": "With aspect ratio",
            "data": {
                "prompt": "A futuristic city skyline",
                "aspect_ratio": "16:9"
            }
        },
        {
            "name": "Full parameters",
            "data": {
                "prompt": "A serene lake with mountains in the background",
                "style": "cinematic",
                "aspect_ratio": "4:3"
            }
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n  Testing: {test_case['name']}")
        try:
            response = requests.post(
                f"{base_url}/v1/images/generate",
                json=test_case["data"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["status", "from_cache", "image_url", "created_at"]
                
                if all(field in data for field in required_fields):
                    if data["status"] == "success":
                        print(f"  ✅ {test_case['name']} passed")
                        print(f"     From cache: {data['from_cache']}")
                        print(f"     Image URL: {data['image_url']}")
                    else:
                        print(f"  ❌ {test_case['name']} failed: status not success")
                        all_passed = False
                else:
                    print(f"  ❌ {test_case['name']} failed: missing required fields")
                    all_passed = False
            else:
                print(f"  ❌ {test_case['name']} failed with status {response.status_code}")
                print(f"     Response: {response.text}")
                all_passed = False
                
        except Exception as e:
            print(f"  ❌ {test_case['name']} failed with error: {e}")
            all_passed = False
    
    return all_passed


def test_invalid_requests(base_url):
    """Test invalid request handling"""
    print("\nTesting invalid request handling...")
    
    invalid_cases = [
        {
            "name": "Empty prompt",
            "data": {"prompt": ""},
            "expected_status": 422
        },
        {
            "name": "Invalid aspect ratio",
            "data": {
                "prompt": "Test prompt",
                "aspect_ratio": "invalid"
            },
            "expected_status": 400
        },
        {
            "name": "Missing prompt",
            "data": {"style": "photorealistic"},
            "expected_status": 422
        }
    ]
    
    all_passed = True
    
    for test_case in invalid_cases:
        print(f"\n  Testing: {test_case['name']}")
        try:
            response = requests.post(
                f"{base_url}/v1/images/generate",
                json=test_case["data"],
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == test_case["expected_status"]:
                print(f"  ✅ {test_case['name']} correctly rejected")
            else:
                print(f"  ❌ {test_case['name']} failed: expected {test_case['expected_status']}, got {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"  ❌ {test_case['name']} failed with error: {e}")
            all_passed = False
    
    return all_passed


def main():
    """Main test function"""
    base_url = "http://localhost:8000"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"Testing Image Generation Microservice at {base_url}")
    print("=" * 60)
    
    # Test health endpoint
    health_ok = test_health_endpoint(base_url)
    
    if not health_ok:
        print("\n❌ Health check failed. Service may not be running.")
        print("Please start the service with:")
        print("python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # Test image generation
    generation_ok = test_image_generation_endpoint(base_url)
    
    # Test invalid requests
    validation_ok = test_invalid_requests(base_url)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if health_ok and generation_ok and validation_ok:
        print("✅ All tests passed!")
        print("\nThe Image Generation Microservice is working correctly.")
        print("Note: Tests ran in demo mode due to missing Google Cloud credentials.")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        print(f"Health check: {'✅' if health_ok else '❌'}")
        print(f"Image generation: {'✅' if generation_ok else '❌'}")
        print(f"Request validation: {'✅' if validation_ok else '❌'}")
        sys.exit(1)


if __name__ == "__main__":
    main()

