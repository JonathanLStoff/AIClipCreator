from clip_creator.ai import find_sections

def main():
    
    with open('test_files/yt_script_t7crKS9DWaI.txt', 'r') as file:
        script = file.read()
    type_phases = "funny moments"
    sections = find_sections(script, type_phases)
    print(sections)
    print(f"Found {len(sections)} sections in the script.")
    
if __name__ == '__main__':
    main()