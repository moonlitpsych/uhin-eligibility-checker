#!/usr/bin/env python3
"""
Parse X12 999 Functional Acknowledgment
Helps understand errors in X12 submissions
"""

def parse_999(x12_999):
    """Parse X12 999 response to understand errors"""
    
    segments = x12_999.split('~')
    errors = []
    
    for segment in segments:
        if segment.startswith('IK3'):
            # IK3 identifies segment with error
            parts = segment.split('*')
            if len(parts) >= 4:
                seg_id = parts[1]  # Segment ID
                position = parts[2]  # Position in transaction
                loop = parts[3] if len(parts) > 3 else ''
                error_code = parts[4] if len(parts) > 4 else ''
                errors.append({
                    'type': 'Segment Error',
                    'segment': seg_id,
                    'position': position,
                    'loop': loop,
                    'code': error_code
                })
                
        elif segment.startswith('IK4'):
            # IK4 identifies element error
            parts = segment.split('*')
            if len(parts) >= 3:
                element_pos = parts[1]  # Element position
                ref_num = parts[2]  # Reference number
                error_code = parts[3] if len(parts) > 3 else ''
                element_copy = parts[4] if len(parts) > 4 else ''
                bad_value = parts[5] if len(parts) > 5 else ''
                errors.append({
                    'type': 'Element Error',
                    'position': element_pos,
                    'error_code': error_code,
                    'element_copy': element_copy,
                    'bad_value': bad_value.rstrip('~')
                })
                
        elif segment.startswith('IK5'):
            # IK5 transaction set response
            parts = segment.split('*')
            if len(parts) >= 2:
                status = parts[1]  # A=Accepted, R=Rejected
                errors.append({
                    'type': 'Transaction Status',
                    'status': 'Rejected' if status == 'R' else 'Accepted'
                })
                
        elif segment.startswith('CTX'):
            # CTX provides context
            parts = segment.split('*')
            if len(parts) > 1:
                context = '*'.join(parts[1:])
                errors.append({
                    'type': 'Context',
                    'info': context
                })
    
    return errors


if __name__ == '__main__':
    # Read the 999 response
    import sys
    from pathlib import Path
    
    # Find the most recent x12_271 file that contains a 999
    output_dir = Path('output')
    x12_files = list(output_dir.glob('x12_271_*.txt'))
    
    if not x12_files:
        print("No X12 271 files found in output/")
        sys.exit(1)
    
    # Get most recent file
    latest_file = sorted(x12_files, key=lambda f: f.stat().st_mtime)[-1]
    
    print(f"Analyzing: {latest_file.name}")
    print("="*60)
    
    with open(latest_file, 'r') as f:
        content = f.read()
    
    # Check if it's a 999
    if 'ST*999' in content:
        print("X12 999 FUNCTIONAL ACKNOWLEDGMENT - ERRORS FOUND")
        print("="*60)
        
        # Extract the payload
        if '<Payload>' in content:
            start = content.find('<Payload>') + 9
            end = content.find('</Payload>')
            x12_999 = content[start:end] if end > start else content
        else:
            x12_999 = content
        
        errors = parse_999(x12_999)
        
        print("\nERRORS IDENTIFIED:")
        for i, error in enumerate(errors, 1):
            if error['type'] == 'Segment Error':
                print(f"\n{i}. SEGMENT ERROR:")
                print(f"   Segment: {error['segment']}")
                print(f"   Position: {error['position']}")
                print(f"   Loop: {error['loop']}")
                print(f"   Code: {error['code']}")
                
            elif error['type'] == 'Element Error':
                print(f"   ELEMENT ERROR:")
                print(f"   Position: {error['position']}")
                print(f"   Error Code: {error['error_code']}")
                if error['element_copy']:
                    print(f"   Element Copy: {error['element_copy']}")
                if error['bad_value']:
                    print(f"   Bad Value: {error['bad_value']}")
                    
            elif error['type'] == 'Context':
                print(f"   Context: {error['info']}")
                
            elif error['type'] == 'Transaction Status':
                print(f"\nTRANSACTION STATUS: {error['status']}")
        
        # Common error codes
        print("\n" + "="*60)
        print("ERROR CODE MEANINGS:")
        print("  I5 = Implementation segment not expected")
        print("  I12 = Implementation 'Not Used' element present") 
        print("  509 = Implementation Not Used")
        print("  66 = Invalid/Missing ID Qualifier")
        print("  67 = Invalid/Missing ID")
        
    else:
        print("This is a valid X12 271 eligibility response (not an error)")
        print("The transaction was successful.")