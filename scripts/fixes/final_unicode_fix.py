#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final comprehensive Unicode character fix
"""

import os
import re
from pathlib import Path

def fix_all_unicode_chars():
    """Fix ALL Unicode characters in Python files"""
    
    # Extended replacement map
    replacements = {
        # Success indicators
        '[SUCCESS]': '[SUCCESS]',
        '[OK]': '[OK]',
        '[CHECKED]': '[CHECKED]',
        
        # Warnings and errors
        '[WARNING]': '[WARNING]',
        '[WARNING]': '[WARNING]',
        '[ERROR]': '[ERROR]',
        '[FAILED]': '[FAILED]',
        '[ALERT]': '[ALERT]',
        '[BLOCKED]': '[BLOCKED]',
        
        # Process indicators
        '[PROCESSING]': '[PROCESSING]',
        '[LOADING]': '[LOADING]',
        '[REFRESH]': '[REFRESH]',
        '[PENDING]': '[PENDING]',
        
        # Info and data
        '[INFO]': '[INFO]',
        '[STATS]': '[STATS]',
        '[DECLINE]': '[DECLINE]',
        '[LIST]': '[LIST]',
        '[DOCUMENT]': '[DOCUMENT]',
        '[THIRD]': '[NOTE]',
        '[DATE]': '[DATE]',
        '[TIME]': '[TIME]',
        
        # Security and networking
        '[SECURE]': '[SECURE]',
        '[UNLOCKED]': '[UNLOCKED]',
        '[KEY]': '[KEY]',
        '[SHIELD]': '[SHIELD]',
        '[NETWORK]': '[NETWORK]',
        '[LINK]': '[LINK]',
        '[SIGNAL]': '[SIGNAL]',
        
        # Features and navigation
        '[FEATURE]': '[FEATURE]',
        '[STAR]': '[STAR]',
        '[TARGET]': '[TARGET]',
        '[EVENT]': '[EVENT]',
        '[DEPLOY]': '[DEPLOY]',
        '[LAUNCH]': '[LAUNCH]',
        '[MAGIC]': '[MAGIC]',
        
        # Health and status
        '[HEALTH]': '[HEALTH]',
        '[HEALTHY]': '[HEALTHY]',
        '[CAUTION]': '[CAUTION]',
        '[WARNING]': '[WARNING]',
        '[SPECIAL]': '[SPECIAL]',
        '[DISABLED]': '[DISABLED]',
        '[NEUTRAL]': '[NEUTRAL]',
        '[INFO]': '[INFO]',
        
        # Actions and tools
        '[TOOL]': '[TOOL]',
        '[BUILD]': '[BUILD]',
        '[SETTINGS]': '[SETTINGS]',
        '[REPAIR]': '[REPAIR]',
        '[CONFIG]': '[CONFIG]',
        '[FAST]': '[FAST]',
        '[HOT]': '[HOT]',
        '[COLD]': '[COLD]',
        
        # Misc symbols
        '[ANNOUNCE]': '[ANNOUNCE]',
        '[BROADCAST]': '[BROADCAST]',
        '[CELEBRATE]': '[CELEBRATE]',
        '[PARTY]': '[PARTY]',
        '[BALLOON]': '[BALLOON]',
        '[TROPHY]': '[TROPHY]',
        '[FIRST]': '[FIRST]',
        '[SECOND]': '[SECOND]',
        '[THIRD]': '[THIRD]',
        
        # Arrows and directions
        '[RIGHT]': '[RIGHT]',
        '[LEFT]': '[LEFT]',
        '[UP]': '[UP]',
        '[DOWN]': '[DOWN]',
        '[UP_RIGHT]': '[UP_RIGHT]',
        '[DOWN_RIGHT]': '[DOWN_RIGHT]',
        '[DOWN_LEFT]': '[DOWN_LEFT]',
        '[UP_LEFT]': '[UP_LEFT]',
        
        # Numbers and counting
        '[1]': '[1]',
        '[2]': '[2]',
        '[3]': '[3]',
        '[4]': '[4]',
        '[5]': '[5]',
        '[6]': '[6]',
        '[7]': '[7]',
        '[8]': '[8]',
        '[9]': '[9]',
        '[10]': '[10]',
        
        # Special characters
        '(C)': '(C)',
        '(R)': '(R)',
        '(TM)': '(TM)',
        '[INFO]': '[INFO]',
        '[RECYCLE]': '[RECYCLE]',
        '[BALANCE]': '[BALANCE]',
        '[SEARCH]': '[SEARCH]',
        '[ZOOM]': '[ZOOM]',
    }
    
    root_dir = Path(__file__).parent.parent.parent
    python_files = list(root_dir.rglob("*.py"))
    files_fixed = 0
    total_replacements = 0
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            file_replacements = 0
            
            # Apply all replacements
            for unicode_char, replacement in replacements.items():
                if unicode_char in content:
                    count = content.count(unicode_char)
                    content = content.replace(unicode_char, replacement)
                    file_replacements += count
                    total_replacements += count
            
            # Also handle any remaining non-ASCII characters in print statements
            # Find print statements with non-ASCII chars
            print_pattern = r'print\([^)]*[^\x00-\x7F][^)]*\)'
            matches = re.findall(print_pattern, content)
            
            for match in matches:
                # Replace any remaining non-ASCII chars with placeholder
                clean_match = re.sub(r'[^\x00-\x7F]', '[CHAR]', match)
                content = content.replace(match, clean_match)
                file_replacements += 1
                total_replacements += 1
            
            if content != original_content:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_fixed += 1
                print(f"[SUCCESS] Fixed {file_replacements} characters in: {py_file}")
        
        except Exception as e:
            print(f"[ERROR] Error processing {py_file}: {e}")
    
    print(f"\n[TARGET] Unicode Fix Summary:")
    print(f"   Files processed: {len(python_files)}")
    print(f"   Files fixed: {files_fixed}")
    print(f"   Total replacements: {total_replacements}")
    
    return files_fixed > 0

if __name__ == "__main__":
    fix_all_unicode_chars()
