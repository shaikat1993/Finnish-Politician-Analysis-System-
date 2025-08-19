#!/usr/bin/env python3
"""
Test script for FPAS API endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_health_endpoint():
    """Test the health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("\n=== Health Endpoint ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_politician_details(politician_id="1302"):
    """Test the politician details endpoint for a specific politician"""
    response = requests.get(f"{BASE_URL}/politicians/{politician_id}/details")
    print(f"\n=== Politician Details for ID: {politician_id} ===")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Print basic info
        print(f"Name: {data.get('name')}")
        print(f"Party: {data.get('party')}")
        print(f"Position: {data.get('position')}")
        
        # Check news sources
        news = data.get('news', [])
        print(f"\nNews Articles: {len(news)}")
        
        # Group by source
        sources = {}
        for article in news:
            source = article.get('source', 'Unknown')
            if source not in sources:
                sources[source] = 0
            sources[source] += 1
        
        print("\nNews Sources Distribution:")
        for source, count in sources.items():
            print(f"- {source}: {count} articles")
        
        # Print a few sample articles
        if news:
            print("\nSample News Articles:")
            for i, article in enumerate(news[:3]):
                print(f"\n{i+1}. {article.get('title')}")
                print(f"   Source: {article.get('source')}")
                print(f"   URL: {article.get('url')}")
                pub_date = article.get('published_date')
                if isinstance(pub_date, str):
                    try:
                        pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                        print(f"   Published: {pub_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    except ValueError:
                        print(f"   Published: {pub_date}")
                else:
                    print(f"   Published: {pub_date}")
    
    return response.status_code == 200

def test_news_by_politician(politician_id="1302"):
    """Test the news by politician endpoint"""
    response = requests.get(f"{BASE_URL}/news/by-politician/{politician_id}")
    print(f"\n=== News for Politician ID: {politician_id} ===")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Print pagination info
        print(f"Page: {data.get('page')}")
        print(f"Total: {data.get('total')}")
        
        # Group by source
        news = data.get('data', [])
        sources = {}
        for article in news:
            source = article.get('source', 'Unknown')
            if source not in sources:
                sources[source] = 0
            sources[source] += 1
        
        print("\nNews Sources Distribution:")
        for source, count in sources.items():
            print(f"- {source}: {count} articles")
    
    return response.status_code == 200

def main():
    """Run all tests"""
    print(f"Testing API endpoints at {BASE_URL}")
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    
    # Test politician details
    politician_details_ok = test_politician_details()
    
    # Test news by politician
    news_by_politician_ok = test_news_by_politician()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Health Endpoint: {'✅ OK' if health_ok else '❌ Failed'}")
    print(f"Politician Details: {'✅ OK' if politician_details_ok else '❌ Failed'}")
    print(f"News by Politician: {'✅ OK' if news_by_politician_ok else '❌ Failed'}")

if __name__ == "__main__":
    main()
