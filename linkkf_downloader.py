#!/usr/bin/env python3
"""
LinkKF Video Downloader

A custom downloader for kr.linkkf.net video streaming site.
Downloads HLS (.m3u8) streams and converts them to MP4 format.
"""

import re
import os
import sys
import json
import time
import random
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup


class LinkKFDownloader:
    """Custom downloader for LinkKF video streaming site."""
    
    def __init__(self, output_dir: str = "./downloads") -> None:
        """
        Initialize the downloader.
        
        Args:
            output_dir: Directory to save downloaded videos
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Origin': 'https://linkkf.live',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if the URL is a valid LinkKF player URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        pattern = r'https://linkkf\.live/player/v\d+-sub-\d+/'
        return bool(re.match(pattern, url))
    
    def extract_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract video information from the player page.
        Enhanced version based on working reference script.
        
        Args:
            url: Player page URL
            
        Returns:
            Dictionary containing video information or None if failed
        """
        if not self.validate_url(url):
            print(f"❌ Invalid URL format: {url}")
            return None
        
        try:
            print(f"🔍 Fetching page: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract video ID from URL for fallback
            video_id_match = re.search(r'v(\d+)-sub-(\d+)', url)
            if not video_id_match:
                print("❌ Could not extract video ID from URL")
                return None
            
            video_id = video_id_match.group(1)
            sub_id = video_id_match.group(2)
            
            # Extract title from page (similar to reference script)
            title_element = soup.find('title')
            if not title_element:
                # Try alternative title extraction
                title_element = soup.find(class_='myui-panel__head')
            
            title = title_element.get_text(strip=True) if title_element else f"video_{video_id}_{sub_id}"
            
            # Enhanced JavaScript parsing (based on reference script approach)
            print("🔍 Analyzing JavaScript for player_post variable...")
            
            # Find player script - look for the specific pattern used in reference
            player_script = None
            scripts = soup.find_all('script')
            
            for script in scripts:
                if script.string and 'player_post' in script.string:
                    player_script = script.string
                    print("✅ Found script with player_post variable")
                    break
            
            if not player_script:
                print("❌ Could not find player_post in JavaScript")
                print("🔍 Trying alternative extraction methods...")
                # Don't return None here, continue with fallback methods
            
            # Extract iframe URL using the reference script method
            iframe_url = None
            
            # Look for player_post variable (reference script approach)
            if player_script:  # Only try if we found player_post
                try:
                    # Find the pattern: player_post = "URL"
                    click_pos = player_script.find('.click')
                    if click_pos != -1:
                        player_post_start = player_script.find('player_post', click_pos) + 13
                        player_post_end = player_script.find(',', player_post_start) - 1
                        iframe_url = player_script[player_post_start:player_post_end].strip('"\'')
                        print(f"✅ Extracted iframe URL via player_post: {iframe_url}")
                except Exception as e:
                    print(f"⚠️  player_post extraction failed: {e}")
            
            # Fallback: Look for iframe elements if player_post method failed
            if not iframe_url:
                print("🔍 Falling back to iframe element search...")
                iframes = soup.find_all('iframe')
                for iframe in iframes:
                    src = iframe.get('src')
                    if src and ('myani.app' in src or 'sub3.top' in src or '.php' in src):
                        iframe_url = src
                        print(f"✅ Found iframe URL: {iframe_url}")
                        break
            
            # Enhanced fallback: Look for different JavaScript patterns
            if not iframe_url:
                print("🔍 Enhanced fallback: Searching for alternative JavaScript patterns...")
                for script in scripts:
                    if script.string:
                        # Look for various iframe URL patterns
                        iframe_patterns = [
                            r'["\']([^"\']*(?:myani\.app|sub3\.top|\.php)[^"\']*)["\']',
                            r'src\s*[:=]\s*["\']([^"\']*(?:myani\.app|sub3\.top)[^"\']*)["\']',
                            r'url\s*[:=]\s*["\']([^"\']*(?:myani\.app|sub3\.top)[^"\']*)["\']'
                        ]
                        
                        for pattern in iframe_patterns:
                            matches = re.findall(pattern, script.string)
                            for match in matches:
                                if 'myani.app' in match or 'sub3.top' in match or '.php' in match:
                                    iframe_url = match
                                    print(f"✅ Found iframe URL via JavaScript pattern: {iframe_url}")
                                    break
                            if iframe_url:
                                break
                    if iframe_url:
                        break
            
            # Final fallback: Try to construct iframe URL based on video ID patterns
            if not iframe_url:
                print("🔧 Final fallback: Attempting to construct iframe URL...")
                
                # Common iframe URL patterns observed
                possible_iframe_urls = [
                    f'https://play.sub3.top/b2/kn1.php?url={video_id}n{sub_id}&id',
                    f'https://g2.myani.app/player.php?url={video_id}s{sub_id}',
                    f'https://play.sub3.top/player.php?url={video_id}s{sub_id}',
                    f'https://play.sub3.top/b2/kn1.php?url={video_id}s{sub_id}&id',
                    f'https://g2.myani.app/b2/kn1.php?url={video_id}n{sub_id}&id'
                ]
                
                for test_iframe_url in possible_iframe_urls:
                    try:
                        print(f"   Testing constructed URL: {test_iframe_url}")
                        test_headers = {
                            'Referer': url,
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        
                        # Quick test to see if the URL responds
                        test_response = self.session.head(test_iframe_url, headers=test_headers, timeout=10)
                        if test_response.status_code == 200:
                            iframe_url = test_iframe_url
                            print(f"✅ Constructed iframe URL works: {iframe_url}")
                            break
                        elif test_response.status_code in [301, 302]:
                            redirect_url = test_response.headers.get('Location')
                            if redirect_url:
                                iframe_url = redirect_url
                                print(f"✅ Found iframe URL via redirect: {iframe_url}")
                                break
                    except Exception as e:
                        print(f"     Failed: {e}")
                        continue
            
            if not iframe_url:
                print("❌ Could not find iframe URL")
                
                # Enhanced debugging: Show what we actually found
                print("🔍 Debug: Page analysis results:")
                print(f"   📝 Page title: {title}")
                print(f"   📊 Total scripts found: {len(scripts)}")
                print(f"   📊 Total iframes found: {len(soup.find_all('iframe'))}")
                
                # Show a sample of the page content for debugging
                print("🔍 Debug: Sample page content (first 500 chars):")
                print(f"   {response.text[:500]}...")
                
                # Check if page is blocked or redirected
                if "cloudflare" in response.text.lower() or "access denied" in response.text.lower():
                    print("⚠️  Page might be blocked by CloudFlare or access control")
                elif "404" in response.text or "not found" in response.text.lower():
                    print("⚠️  Page might be returning 404 or not found")
                elif len(response.text) < 1000:
                    print("⚠️  Page content is unusually short - might be an error page")
                
                return None
            
            # Extract player_data_url from iframe URL
            player_data_url = None
            url_param_match = re.search(r'[?&]url=([^&]+)', iframe_url)
            if url_param_match:
                player_data_url = url_param_match.group(1)
                print(f"✅ Extracted player_data URL: {player_data_url}")
            
            if not player_data_url:
                print("❌ Could not extract player_data URL from iframe")
                return None
            
            # Fetch iframe page and extract M3U8 URL (reference script approach)
            print(f"🔍 Fetching iframe page: {iframe_url}")
            
            # Enhanced headers for iframe request
            iframe_headers = {
                'Referer': 'https://linkkf.live/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
            }
            
            iframe_response = self.session.get(iframe_url, timeout=30, headers=iframe_headers)
            iframe_response.raise_for_status()
            
            iframe_soup = BeautifulSoup(iframe_response.text, 'html.parser')
            
            # Direct approach: Find source element (reference script method)
            m3u8_url = None
            source_element = iframe_soup.find('source')
            
            if source_element and source_element.get('src'):
                m3u8_url = source_element.get('src')
                print(f"✅ Found M3U8 URL directly from source element: {m3u8_url}")
            
            # Fallback: Look in video elements
            if not m3u8_url:
                print("🔍 Searching in video elements...")
                video_elements = iframe_soup.find_all('video')
                for video in video_elements:
                    sources = video.find_all('source')
                    for source in sources:
                        src = source.get('src')
                        if src and ('.m3u8' in src or src.startswith('http')):
                            m3u8_url = src
                            print(f"✅ Found M3U8 URL in video element: {m3u8_url}")
                            break
                    if m3u8_url:
                        break
            
            # Enhanced fallback: Look in scripts for M3U8 URLs
            if not m3u8_url:
                print("🔍 Searching in iframe scripts...")
                iframe_scripts = iframe_soup.find_all('script')
                for script in iframe_scripts:
                    if script.string:
                        # Look for various M3U8 URL patterns
                        m3u8_patterns = [
                            r'["\']([^"\']*\.m3u8[^"\']*)["\']',
                            r'src\s*[:=]\s*["\']([^"\']*\.m3u8[^"\']*)["\']',
                            r'https?://[^\s"\']+\.m3u8[^\s"\']*'
                        ]
                        
                        for pattern in m3u8_patterns:
                            matches = re.findall(pattern, script.string)
                            if matches:
                                test_url = matches[0] if isinstance(matches[0], str) else matches[0]
                                if test_url and '.m3u8' in test_url:
                                    m3u8_url = test_url
                                    print(f"✅ Found M3U8 URL in iframe script: {m3u8_url}")
                                    break
                        if m3u8_url:
                            break
            
            # Smart construction based on patterns (enhanced with reference knowledge)
            if not m3u8_url:
                print("🔧 Constructing M3U8 URL using enhanced patterns...")
                
                # Enhanced patterns based on analysis of both scripts
                possible_patterns = []
                
                # Determine base domain from iframe URL
                iframe_domain = iframe_url.split('/')[2] if '/' in iframe_url else ''
                
                if 'myani.app' in iframe_domain:
                    # MyAni.app patterns (most common from reference)
                    possible_patterns.extend([
                        f'https://m3k.myani.app/b2nss4/m3u8/{player_data_url}.m3u8',
                        f'https://m3k.myani.app/b2k37/m3u8/{player_data_url}.m3u8',
                        f'https://m3k.myani.app/b2k28/m3u8/{player_data_url}.m3u8',
                        f'https://m3k.myani.app/b2/m3u8/{player_data_url}.m3u8',
                        f'https://g2.myani.app/hls/{player_data_url}/index.m3u8',
                        f'https://g2.myani.app/stream/{player_data_url}/index.m3u8'
                    ])
                elif 'sub3.top' in iframe_domain:
                    # Sub3.top patterns with more variations
                    # Try both 'n' and 's' patterns since different regions might use different patterns
                    base_id = player_data_url[:-2] if player_data_url.endswith(('n1', 's1', 'n2', 's2')) else player_data_url
                    
                    possible_patterns.extend([
                        f'https://bn1.imgkr4.top/file/k0625n1/{player_data_url}/index.m3u8',
                        f'https://bn2.imgkr4.top/file/k0625n1/{player_data_url}/index.m3u8',
                        f'https://bn3.imgkr4.top/file/k0625n1/{player_data_url}/index.m3u8',
                        f'https://play.sub3.top/hls/{player_data_url}/index.m3u8',
                        f'https://play.sub3.top/stream/{player_data_url}/index.m3u8',
                        f'https://sub3.top/hls/{player_data_url}/index.m3u8',
                        f'https://m3k.myani.app/b2nss4/m3u8/{player_data_url}.m3u8',
                        f'https://g2.myani.app/hls/{player_data_url}/index.m3u8',
                        # Try alternative patterns (n->s, s->n conversion)
                        f'https://m3k.myani.app/b2nss4/m3u8/{base_id}s1.m3u8' if 'n1' in player_data_url else f'https://m3k.myani.app/b2nss4/m3u8/{base_id}n1.m3u8',
                        f'https://bn1.imgkr4.top/file/k0625n1/{base_id}s1/index.m3u8' if 'n1' in player_data_url else f'https://bn1.imgkr4.top/file/k0625n1/{base_id}n1/index.m3u8'
                    ])
                else:
                    # Generic fallback patterns with more options
                    possible_patterns.extend([
                        f'https://m3k.myani.app/b2nss4/m3u8/{player_data_url}.m3u8',
                        f'https://bn1.imgkr4.top/file/k0625n1/{player_data_url}/index.m3u8',
                        f'https://bn2.imgkr4.top/file/k0625n1/{player_data_url}/index.m3u8',
                        f'https://bn3.imgkr4.top/file/k0625n1/{player_data_url}/index.m3u8',
                        f'https://play.sub3.top/hls/{player_data_url}/index.m3u8',
                        f'https://g2.myani.app/hls/{player_data_url}/index.m3u8',
                        f'https://m3k.myani.app/b2k37/m3u8/{player_data_url}.m3u8'
                    ])
                
                # Cross-pattern matching: if 'n' pattern fails, try 's' pattern
                if player_data_url.endswith(('n1', 'n2', 'n3', 'n4', 'n5', 'n6')):
                    # Convert 401801n2 -> 401801s2
                    s_pattern = player_data_url[:-2] + 's' + player_data_url[-1]
                    possible_patterns.extend([
                        f'https://m3k.myani.app/b2nss4/m3u8/{s_pattern}.m3u8',
                        f'https://m3k.myani.app/b2k37/m3u8/{s_pattern}.m3u8',
                        f'https://m3k.myani.app/b2k28/m3u8/{s_pattern}.m3u8',
                        f'https://m3k.myani.app/b2/m3u8/{s_pattern}.m3u8',
                        f'https://g2.myani.app/hls/{s_pattern}/index.m3u8',
                        f'https://bi1.imgkr2.top/file/ns2bb4/{s_pattern}/index.m3u8',
                        f'https://bi2.imgkr2.top/file/ns2bb4/{s_pattern}/index.m3u8',
                    ])
                elif player_data_url.endswith(('s1', 's2', 's3', 's4', 's5', 's6')):
                    # Convert 401801s2 -> 401801n2
                    n_pattern = player_data_url[:-2] + 'n' + player_data_url[-1]
                    possible_patterns.extend([
                        f'https://bn1.imgkr4.top/file/k0625n1/{n_pattern}/index.m3u8',
                        f'https://play.sub3.top/hls/{n_pattern}/index.m3u8',
                        f'https://play.sub3.top/stream/{n_pattern}/index.m3u8',
                    ])
                
                print(f"🔍 Testing {len(possible_patterns)} possible M3U8 URLs...")
                for test_url in possible_patterns:
                    try:
                        print(f"   Testing: {test_url}")
                        test_headers = {
                            'Referer': iframe_url,
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        
                        # Try HEAD request first for efficiency
                        test_response = self.session.head(test_url, timeout=10, headers=test_headers)
                        
                        if test_response.status_code == 200:
                            m3u8_url = test_url
                            print(f"✅ Found working M3U8 URL: {m3u8_url}")
                            break
                        elif test_response.status_code in [301, 302]:
                            redirect_url = test_response.headers.get('Location')
                            if redirect_url:
                                print(f"     Following redirect: {redirect_url}")
                                
                                # Validate redirect URL - reject invalid domains
                                invalid_domains = ['google.com', 'microsoft.com', 'amazon.com', 'cloudflare.com']
                                if any(domain in redirect_url.lower() for domain in invalid_domains):
                                    print(f"     ❌ Invalid redirect to: {redirect_url}")
                                    continue
                                
                                # Check if redirect URL looks like a valid M3U8 URL
                                if not ('.m3u8' in redirect_url or 'myani.app' in redirect_url or 'imgkr' in redirect_url):
                                    print(f"     ❌ Redirect doesn't look like M3U8: {redirect_url}")
                                    continue
                                
                                redirect_response = self.session.head(redirect_url, timeout=10, headers=test_headers)
                                if redirect_response.status_code == 200:
                                    m3u8_url = redirect_url
                                    print(f"✅ Found working M3U8 URL after redirect: {m3u8_url}")
                                    break
                        else:
                            print(f"     Status: {test_response.status_code}")
                            
                    except Exception as e:
                        print(f"     Error: {e}")
                        continue
            
            if not m3u8_url:
                print("❌ Could not find or construct M3U8 URL")
                return None
            
            # Clean title for filename (reference script approach)
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)  # Only replace truly problematic characters
            safe_title = re.sub(r'_+', '_', safe_title).strip('_')
            safe_title = re.sub(r'\s*Linkkf\s*$', '', safe_title, flags=re.IGNORECASE)
            safe_title = safe_title.strip()
            
            # Remove subtitle suffix and clean up
            safe_title = re.sub(r'-자막$', '', safe_title)
            safe_title = safe_title.strip()
            
            # Minimal cleanup for file system compatibility - preserve spaces and readable format
            safe_title = re.sub(r"[']", '', safe_title)  # Remove apostrophes only (A's -> As)
            safe_title = re.sub(r'\s+', ' ', safe_title)  # Normalize multiple spaces to single space
            safe_title = safe_title[:100]  # Reasonable filename length limit
            safe_title = safe_title.strip()  # Remove leading/trailing spaces
            
            # Extract subtitle URL (reference script feature)
            subtitle_url = None
            try:
                track_element = iframe_soup.find('track')
                if track_element and track_element.get('src'):
                    sub_src = track_element.get('src')
                    if sub_src.startswith('http'):
                        subtitle_url = sub_src
                    else:
                        # Make relative URL absolute
                        iframe_base = f"https://{iframe_url.split('/')[2]}"
                        subtitle_url = iframe_base + sub_src
                    print(f"✅ Found subtitle URL: {subtitle_url}")
            except Exception as e:
                print(f"⚠️  Subtitle extraction failed: {e}")
            
            # Enhanced subtitle fallback - construct subtitle URL from player_data_url
            if not subtitle_url and player_data_url:
                print("🔍 Trying to construct subtitle URL...")
                
                # Common subtitle URL patterns based on different iframe domains
                possible_subtitle_urls = []
                
                if 'myani.app' in iframe_domain:
                    possible_subtitle_urls = [
                        f'https://k1.sub1.top/s/{player_data_url}.vtt',
                        f'https://k2.sub1.top/s/{player_data_url}.vtt',
                        f'https://sub1.top/s/{player_data_url}.vtt'
                    ]
                elif 'sub3.top' in iframe_domain:
                    possible_subtitle_urls = [
                        f'https://2.sub2.top/s/{player_data_url}.vtt',
                        f'https://1.sub2.top/s/{player_data_url}.vtt',
                        f'https://sub2.top/s/{player_data_url}.vtt',
                        f'https://k1.sub1.top/s/{player_data_url}.vtt'
                    ]
                else:
                    # Generic fallback
                    possible_subtitle_urls = [
                        f'https://k1.sub1.top/s/{player_data_url}.vtt',
                        f'https://2.sub2.top/s/{player_data_url}.vtt',
                        f'https://1.sub2.top/s/{player_data_url}.vtt',
                        f'https://sub1.top/s/{player_data_url}.vtt',
                        f'https://sub2.top/s/{player_data_url}.vtt'
                    ]
                
                # Test each possible subtitle URL
                for test_sub_url in possible_subtitle_urls:
                    try:
                        print(f"   Testing subtitle: {test_sub_url}")
                        sub_headers = {
                            'Referer': iframe_url,
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        
                        # Quick test to see if subtitle exists
                        sub_response = self.session.head(test_sub_url, headers=sub_headers, timeout=10)
                        if sub_response.status_code == 200:
                            subtitle_url = test_sub_url
                            print(f"✅ Found subtitle URL: {subtitle_url}")
                            break
                    except Exception as e:
                        print(f"     Subtitle test failed: {e}")
                        continue
            
            video_info = {
                'url': url,
                'video_id': video_id,
                'sub_id': sub_id,
                'title': title,
                'safe_title': safe_title,
                'player_data_url': player_data_url,
                'iframe_url': iframe_url,
                'm3u8_url': m3u8_url,
                'subtitle_url': subtitle_url,
                'filename': f"{safe_title}.mp4"
            }
            
            print(f"✅ Enhanced video info extracted:")
            print(f"   📝 Title: {title}")
            print(f"   🆔 ID: {video_id}-{sub_id}")
            print(f"   🎬 Player Data URL: {player_data_url}")
            print(f"   🖼️  Iframe URL: {iframe_url}")
            print(f"   🔗 M3U8: {m3u8_url}")
            if subtitle_url:
                print(f"   📄 Subtitle: {subtitle_url}")
            
            return video_info
            
        except requests.RequestException as e:
            print(f"❌ Network error: {e}")
            return None
        except Exception as e:
            print(f"❌ Error extracting video info: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def download_m3u8_segments_advanced(self, m3u8_url: str, output_file: str, referer: str = None) -> bool:
        """
        Advanced M3U8 download with bypass techniques for protected streams.
        Enhanced to handle both video segments (.ts) and image segments (.jpg/.png).
        
        Args:
            m3u8_url: URL of the m3u8 playlist
            output_file: Output file path
            referer: Referer URL for requests
            
        Returns:
            True if successful, False otherwise
        """
        print(f"🚀 Advanced M3U8 Download: {m3u8_url}")
        
        try:
            # Browser profiles for fingerprint evasion
            browser_profiles = [
                {
                    'name': 'Chrome Windows',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    'accept_language': 'ko-KR,ko;q=0.9,en;q=0.8'
                },
                {
                    'name': 'Firefox Windows', 
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
                    'accept_language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3'
                },
                {
                    'name': 'Safari macOS',
                    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
                    'accept_language': 'ko-KR,ko;q=0.9,en;q=0.8'
                },
                {
                    'name': 'VLC Player',
                    'user_agent': 'VLC media player - version 3.0.18 Vetinari - (c) 1996-2022 the VideoLAN team',
                    'accept_language': 'ko-KR,ko;q=0.9,en;q=0.8'
                },
                {
                    'name': 'FFmpeg',
                    'user_agent': 'Lavf/58.76.100',
                    'accept_language': 'ko-KR,ko;q=0.9,en;q=0.8'
                }
            ]
            
            def get_advanced_headers(profile: Dict[str, str], referer: str = None) -> Dict[str, str]:
                """Generate advanced headers for bypass."""
                headers = {
                    'User-Agent': profile['user_agent'],
                    'Accept': '*/*',
                    'Accept-Language': profile['accept_language'],
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'cross-site',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
                
                if referer:
                    headers['Referer'] = referer
                
                # Extract domain and set Origin header
                from urllib.parse import urlparse
                parsed_url = urlparse(m3u8_url)
                headers['Origin'] = f"{parsed_url.scheme}://{parsed_url.netloc}"
                
                return headers
            
            def detect_content_type(content: str) -> str:
                """Detect if content is M3U8 playlist or blocked."""
                content_lower = content.lower().strip()
                
                if content_lower.startswith('#extm3u'):
                    return 'M3U8'
                elif content_lower.startswith('<!doctype html') or content_lower.startswith('<html'):
                    return 'HTML'
                elif 'google.com' in content_lower or 'cloudflare' in content_lower:
                    return 'BLOCKED'
                else:
                    return 'UNKNOWN'
            
            # Try different methods to access the playlist
            success = False
            playlist_content = ""
            successful_method = ""
            
            # Method 1: Try all browser profiles
            for i, profile in enumerate(browser_profiles):
                try:
                    print(f"🔄 Trying method {i+1}: {profile['name']}")
                    headers = get_advanced_headers(profile, referer)
                    
                    response = self.session.get(
                        m3u8_url,
                        headers=headers,
                        timeout=30,
                        verify=False,
                        allow_redirects=True
                    )
                    
                    print(f"📊 Status: {response.status_code}, Content-Length: {len(response.content)}")
                    
                    if response.status_code == 200:
                        content = response.text
                        content_type = detect_content_type(content)
                        
                        print(f"📄 Content type: {content_type}")
                        
                        if content_type == 'M3U8':
                            print(f"✅ Success with {profile['name']}")
                            success = True
                            playlist_content = content
                            successful_method = profile['name']
                            break
                        else:
                            print(f"⚠️  {profile['name']} returned {content_type}")
                            if i == 0:  # Show preview for first attempt
                                print(f"📄 Content preview: {content[:200]}...")
                    
                    # No delay for maximum speed
                    
                except Exception as e:
                    print(f"❌ {profile['name']} failed: {e}")
                    continue
            
            # Method 2: Try CloudFlare bypass techniques
            if not success:
                print("🛡️  Trying CloudFlare bypass...")
                countries = ['KR', 'US', 'JP', 'SG']
                
                for country in countries:
                    try:
                        profile = browser_profiles[0]  # Use Chrome
                        headers = get_advanced_headers(profile, referer)
                        
                        # Add CloudFlare bypass headers
                        headers.update({
                            'CF-IPCountry': country,
                            'X-Forwarded-For': f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
                            'CF-RAY': f"{random.randint(100000,999999)}-ICN",
                            'Accept-Language': f"{country.lower()}-{country},{country.lower()};q=0.9,en;q=0.8"
                        })
                        
                        print(f"🌍 Trying CF bypass for {country}...")
                        
                        response = self.session.get(
                            m3u8_url,
                            headers=headers,
                            timeout=30,
                            verify=False,
                            allow_redirects=True
                        )
                        
                        if response.status_code == 200:
                            content = response.text
                            if detect_content_type(content) == 'M3U8':
                                print(f"✅ CF bypass successful for {country}")
                                success = True
                                playlist_content = content
                                successful_method = f"CloudFlare bypass ({country})"
                                break
                        
                        # No delay for maximum speed
                        
                    except Exception as e:
                        print(f"❌ CF bypass {country} failed: {e}")
                        continue
            
            if not success:
                print("❌ All advanced methods failed to retrieve valid M3U8 playlist")
                return False
            
            print(f"✅ Retrieved playlist using: {successful_method}")
            print(f"📊 Playlist size: {len(playlist_content)} characters")
            
            # Enhanced segment extraction with type detection
            base_path = m3u8_url.rsplit('/', 1)[0] + '/'
            segments = []
            segment_durations = []
            
            lines = playlist_content.split('\n')
            current_duration = 5.0  # Default duration
            
            for line in lines:
                line = line.strip()
                
                # Extract duration from EXTINF lines
                if line.startswith('#EXTINF:'):
                    try:
                        duration_str = line.split(':')[1].split(',')[0]
                        current_duration = float(duration_str)
                    except:
                        current_duration = 5.0
                
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith('http'):
                    segments.append(line)
                    segment_durations.append(current_duration)
                else:
                    if line.startswith('/'):
                        # Root-relative URL
                        from urllib.parse import urlparse
                        parsed_base = urlparse(m3u8_url)
                        segment_url = f"{parsed_base.scheme}://{parsed_base.netloc}{line}"
                    else:
                        # Relative URL
                        from urllib.parse import urljoin
                        segment_url = urljoin(base_path, line)
                    
                    segments.append(segment_url)
                    segment_durations.append(current_duration)
            
            if not segments:
                print("❌ No segments found in playlist")
                print(f"📄 Playlist content:\n{playlist_content}")
                return False
            
            # Detect segment type
            is_image_based = False
            if segments:
                first_segment = segments[0].lower()
                if first_segment.endswith('.jpg') or first_segment.endswith('.png') or first_segment.endswith('.jpeg'):
                    is_image_based = True
                    print(f"🖼️  Detected image-based stream (slideshow)")
                else:
                    print(f"🎬 Detected video-based stream")
            
            print(f"📋 Found {len(segments)} segments")
            print(f"📋 Sample segments: {segments[:3]}")
            
            # Create temporary directory
            temp_dir = self.output_dir / "temp_segments"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # Advanced segment downloading
                successful_files = []
                successful_durations = []
                failed_count = 0
                
                def download_segment_advanced(index_url_tuple):
                    index, segment_url = index_url_tuple
                    
                    # Determine file extension based on URL
                    if segment_url.lower().endswith('.jpg') or segment_url.lower().endswith('.jpeg'):
                        ext = '.jpg'
                    elif segment_url.lower().endswith('.png'):
                        ext = '.png'
                    else:
                        ext = '.ts'  # Default for video segments
                    
                    segment_file = temp_dir / f"segment_{index:05d}{ext}"
                    
                    # Try multiple profiles for robustness
                    for profile in browser_profiles[:3]:  # Try first 3 profiles
                        try:
                            headers = get_advanced_headers(profile, referer)
                            
                            # Add randomization to avoid detection
                            headers['X-Request-ID'] = f"{random.randint(100000,999999)}"
                            
                            response = self.session.get(
                                segment_url,
                                headers=headers,
                                timeout=60,
                                verify=False,
                                allow_redirects=True,
                                stream=True
                            )
                            
                            response.raise_for_status()
                            
                            # Verify content type
                            content_type = response.headers.get('content-type', '').lower()
                            if 'html' in content_type:
                                print(f"⚠️  Segment {index} returned HTML, trying next profile...")
                                continue
                            
                            # Write file in chunks with maximum speed
                            with open(segment_file, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=65536):
                                    if chunk:
                                        f.write(chunk)
                            
                            # Verify file was written successfully
                            if segment_file.exists() and segment_file.stat().st_size > 0:
                                return segment_file, segment_durations[index], None
                            else:
                                print(f"⚠️  Empty file for segment {index}, trying next profile...")
                                continue
                                
                        except Exception as e:
                            print(f"❌ Profile {profile['name']} failed for segment {index}: {e}")
                            # No delay for maximum speed
                            continue
                    
                    return None, 0, f"All profiles failed for segment {index}"
                
                print("⬇️  Downloading segments with advanced techniques...")
                
                # Aggressive optimization for maximum speed
                with ThreadPoolExecutor(max_workers=8) as executor:
                    futures = {
                        executor.submit(download_segment_advanced, (i, url)): i 
                        for i, url in enumerate(segments)
                    }
                    
                    for future in as_completed(futures):
                        segment_file, duration, error = future.result()
                        
                        if segment_file:
                            successful_files.append(segment_file)
                            successful_durations.append(duration)
                            print(f"✅ Downloaded segment {len(successful_files)}/{len(segments)}")
                        else:
                            failed_count += 1
                            print(f"❌ {error}")
                        
                        # Progress indicator with success rate
                        completed = len(successful_files) + failed_count
                        progress = (completed / len(segments)) * 100
                        success_rate = len(successful_files) / completed if completed > 0 else 0
                        print(f"\r📊 Progress: {progress:.1f}% - Success Rate: {success_rate:.1%}", end='')
                        
                        # Minimal delay for maximum speed
                        time.sleep(random.uniform(0.01, 0.05))
                
                print()  # New line after progress
                
                # Check final success rate
                final_success_rate = len(successful_files) / len(segments)
                print(f"📊 Final success rate: {final_success_rate:.1%}")
                
                if final_success_rate < 0.6:  # Less than 60% success
                    print("❌ Too many segments failed to download")
                    return False
                
                if not successful_files:
                    print("❌ No segments downloaded successfully")
                    return False
                
                # Sort files by name to maintain order
                file_duration_pairs = list(zip(successful_files, successful_durations))
                file_duration_pairs.sort(key=lambda x: x[0].name)
                successful_files = [pair[0] for pair in file_duration_pairs]
                successful_durations = [pair[1] for pair in file_duration_pairs]
                
                # Merge segments
                print("🔗 Merging segments...")
                if is_image_based:
                    return self._merge_images_to_video(successful_files, successful_durations, output_file)
                else:
                    return self._merge_segments_with_ffmpeg(successful_files, output_file)
                
            finally:
                # Cleanup temporary files
                try:
                    for file in temp_dir.glob("segment_*.*"):
                        file.unlink()
                    temp_dir.rmdir()
                except Exception as e:
                    print(f"⚠️  Warning: Could not clean up temp files: {e}")
            
        except Exception as e:
            print(f"❌ Advanced download failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _merge_segments_with_ffmpeg(self, segment_files: List[Path], output_file: str) -> bool:
        """
        Merge video segments using ffmpeg.
        
        Args:
            segment_files: List of segment file paths
            output_file: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import subprocess
            
            # Check for local ffmpeg.exe first, then current directory, then system PATH
            local_ffmpeg = Path(__file__).parent / "ffmpeg.exe"
            cwd_ffmpeg = Path.cwd() / "ffmpeg.exe"
            
            if local_ffmpeg.exists():
                ffmpeg_cmd = str(local_ffmpeg)
                print(f"🎬 Using script directory FFmpeg: {ffmpeg_cmd}")
            elif cwd_ffmpeg.exists():
                ffmpeg_cmd = str(cwd_ffmpeg)
                print(f"🎬 Using current directory FFmpeg: {ffmpeg_cmd}")
            else:
                ffmpeg_cmd = 'ffmpeg'
                print(f"🎬 Using system FFmpeg")
            
            # Create file list for ffmpeg
            file_list_path = self.output_dir / "filelist.txt"
            
            with open(file_list_path, 'w', encoding='utf-8') as f:
                for segment_file in segment_files:
                    # Use absolute path and escape for ffmpeg
                    abs_path = segment_file.absolute()
                    f.write(f"file '{abs_path}'\n")
            
            # Run ffmpeg to merge segments with speed optimization
            cmd = [
                ffmpeg_cmd,  # Use determined ffmpeg command
                '-f', 'concat',
                '-safe', '0',
                '-i', str(file_list_path),
                '-c', 'copy',
                '-threads', '0',  # Use all available CPU cores
                '-y',  # Overwrite output file
                output_file
            ]
            
            print(f"🎬 Running ffmpeg: {' '.join(cmd)}")
            
            # Run with proper encoding handling for Windows and hide window
            import platform
            
            # Hide window on Windows
            creation_flags = 0
            if platform.system() == 'Windows':
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',  # Ignore encoding errors
                timeout=300,  # 5 minutes timeout
                creationflags=creation_flags
            )
            
            # Clean up file list
            try:
                file_list_path.unlink()
            except Exception:
                pass
            
            if result.returncode == 0:
                print(f"✅ Video merged successfully: {output_file}")
                return True
            else:
                # Handle stderr encoding safely
                try:
                    error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                    print(f"❌ FFmpeg error: {error_msg}")
                except (UnicodeDecodeError, UnicodeEncodeError):
                    print("❌ FFmpeg error: (encoding issue in error message)")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ FFmpeg timeout")
            return False
        except FileNotFoundError:
            print("❌ FFmpeg not found. Please install FFmpeg.")
            return False
        except Exception as e:
            print(f"❌ Error merging segments: {e}")
            return False
    
    def _merge_images_to_video(self, image_files: List[Path], durations: List[float], output_file: str) -> bool:
        """
        Merge image files into a video using ffmpeg with individual durations.
        
        Args:
            image_files: List of image file paths
            durations: List of durations for each image
            output_file: Output video file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import subprocess
            
            print(f"🖼️  Converting {len(image_files)} images to video...")
            
            # Check for local ffmpeg.exe first, then current directory, then system PATH
            local_ffmpeg = Path(__file__).parent / "ffmpeg.exe"
            cwd_ffmpeg = Path.cwd() / "ffmpeg.exe"
            
            if local_ffmpeg.exists():
                ffmpeg_cmd = str(local_ffmpeg)
                print(f"🎬 Using script directory FFmpeg: {ffmpeg_cmd}")
            elif cwd_ffmpeg.exists():
                ffmpeg_cmd = str(cwd_ffmpeg)
                print(f"🎬 Using current directory FFmpeg: {ffmpeg_cmd}")
            else:
                ffmpeg_cmd = 'ffmpeg'
                print(f"🎬 Using system FFmpeg")
            
            # Create a safe temporary directory in the system temp folder to avoid path issues
            import tempfile
            with tempfile.TemporaryDirectory(prefix="linkkf_") as temp_dir_path:
                temp_dir = Path(temp_dir_path)
                
                # Copy images to temp directory with simple names
                temp_images = []
                print(f"📁 Preparing {len(image_files)} images for conversion...")
                
                for i, (image_file, duration) in enumerate(zip(image_files, durations)):
                    # Use simple numbered names to avoid path issues
                    temp_image = temp_dir / f"img_{i:05d}.jpg"
                    
                    # Copy image to temp location
                    import shutil
                    shutil.copy2(image_file, temp_image)
                    temp_images.append((temp_image, duration))
                
                # Create concat file with simple paths
                concat_file_path = temp_dir / "concat_list.txt"
                
                with open(concat_file_path, 'w', encoding='utf-8') as f:
                    for temp_image, duration in temp_images:
                        # Use simple relative paths
                        f.write(f"file '{temp_image.name}'\n")
                        f.write(f"duration {duration}\n")
                    
                    # Add the last image again to ensure proper ending
                    if temp_images:
                        last_image = temp_images[-1][0]
                        f.write(f"file '{last_image.name}'\n")
                
                # Run ffmpeg to create video from images with optimized speed settings
                cmd = [
                    ffmpeg_cmd,  # Use determined ffmpeg command
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', str(concat_file_path),
                    '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2',  # 720p instead of 1080p
                    '-r', '30',  # 30 FPS for smooth playback
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',  # Much faster encoding
                    '-crf', '28',  # Slightly lower quality for speed
                    '-pix_fmt', 'yuv420p',
                    '-threads', '0',  # Use all available CPU cores
                    '-y',  # Overwrite output file
                    str(Path(output_file).absolute())  # Use absolute path for output
                ]
                
                print(f"🎬 Running ffmpeg to convert images to video...")
                print(f"🎬 Optimized for speed: 720p, 30fps, ultrafast preset")
                print(f"🎬 Working directory: {temp_dir}")
                
                # Hide window on Windows
                import platform
                creation_flags = 0
                if platform.system() == 'Windows':
                    creation_flags = subprocess.CREATE_NO_WINDOW
                
                # Change working directory to temp dir for relative paths
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=600,  # 10 minutes timeout for image processing
                    creationflags=creation_flags,
                    cwd=temp_dir  # Set working directory
                )
                
                # Temporary directory and files are automatically cleaned up
            
            if result.returncode == 0:
                print(f"✅ Images converted to video successfully: {output_file}")
                return True
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                print(f"❌ FFmpeg error: {error_msg}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ FFmpeg timeout during image conversion")
            return False
        except FileNotFoundError:
            print("❌ FFmpeg not found. Please install FFmpeg.")
            return False
        except Exception as e:
            print(f"❌ Error converting images to video: {e}")
            return False
    
    def download_subtitle(self, subtitle_url: str, video_file_path: Path) -> bool:
        """
        Download subtitle file (.vtt) for the video.
        
        Args:
            subtitle_url: URL of the subtitle file
            video_file_path: Path of the video file (to generate subtitle filename)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"📄 Downloading subtitle: {subtitle_url}")
            
            # Generate subtitle filename based on video filename
            video_path = Path(video_file_path)
            subtitle_path = video_path.with_suffix('.vtt')
            
            # Download subtitle with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Referer': 'https://linkkf.live/',
                'Accept': 'text/vtt,text/plain,*/*',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8'
            }
            
            response = self.session.get(subtitle_url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            # Save subtitle file
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"✅ Subtitle downloaded: {subtitle_path.name}")
            return True
            
        except Exception as e:
            print(f"⚠️  Subtitle download failed: {e}")
            return False
    
    def download_video(self, url: str) -> bool:
        """
        Download video from LinkKF URL.
        
        Args:
            url: LinkKF player URL
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        print(f"🚀 Starting download from: {url}")
        
        # Extract video information
        video_info = self.extract_video_info(url)
        if not video_info:
            return False
        
        # Set output file path and ensure directory exists
        output_file = self.output_dir / video_info['filename']
        
        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory: {output_file.parent}")
        print(f"💾 Output file: {output_file}")
        
        # Download video
        success = self.download_m3u8_segments_advanced(
            video_info['m3u8_url'], 
            str(output_file), 
            video_info.get('iframe_url', url)  # Use iframe URL as referer if available
        )
        
        # Download subtitle if available
        if success and video_info.get('subtitle_url'):
            self.download_subtitle(video_info['subtitle_url'], output_file)
        
        if success:
            file_size = output_file.stat().st_size if output_file.exists() else 0
            elapsed_time = time.time() - start_time
            
            print(f"🎉 Download completed!")
            print(f"   📁 File: {output_file}")
            print(f"   📏 Size: {file_size / 1024 / 1024:.2f} MB")
            print(f"   ⏱️  Time: {elapsed_time:.2f} seconds")
        else:
            print(f"❌ Download failed!")
        
        return success


def main() -> None:
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print("Usage: python linkkf_downloader.py <URL> [output_dir]")
        print("Example: python linkkf_downloader.py 'https://kr.linkkf.net/player/v386192-sub-1/'")
        sys.exit(1)
    
    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./downloads"
    
    downloader = LinkKFDownloader(output_dir)
    success = downloader.download_video(url)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 