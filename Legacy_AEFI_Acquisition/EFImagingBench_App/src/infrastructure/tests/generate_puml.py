import json
import sys
from pathlib import Path
import argparse

def generate_puml(json_path: str):
    path = Path(json_path)
    if not path.exists():
        print(f"Error: File {json_path} not found.")
        return

    with open(path, 'r') as f:
        data = json.load(f)

    test_name = data.get("test_name", "Unknown Test")
    interactions = data.get("interactions", [])
    
    puml_lines = []
    puml_lines.append("@startuml")
    puml_lines.append(f"title Sequence Diagram: {test_name}")
    puml_lines.append("autonumber")
    puml_lines.append("skinparam responseMessageBelowArrow true")
    
    # Identify all participants to declare them (optional, but good for ordering if needed)
    # For now, we'll let PlantUML handle implicit creation
    
    for interaction in interactions:
        actor = interaction.get("actor", "Unknown")
        target = interaction.get("target", "Unknown")
        action = interaction.get("action", "ACTION")
        message = interaction.get("message", "")
        payload = interaction.get("data")
        expect = interaction.get("expect")
        got = interaction.get("got")
        
        # Format the arrow based on action type
        arrow = "->"
        if action in ["RETURN", "REPLY"]:
            arrow = "-->"
        
        # Construct the line
        line = f'"{actor}" {arrow} "{target}" : **{action}** {message}'
        puml_lines.append(line)
        
        # Add note with details if present
        note_lines = []
        if payload:
            import json as j
            # Pretty print JSON payload if it's a dict/list, otherwise str
            payload_str = j.dumps(payload, indent=2) if isinstance(payload, (dict, list)) else str(payload)
            # Truncate if too long
            if len(payload_str) > 200:
                payload_str = payload_str[:200] + "..."
            note_lines.append(f"Data: {payload_str}")
            
        if expect is not None:
            note_lines.append(f"Expect: {expect}")
        if got is not None:
            note_lines.append(f"Got: {got}")
            
        if note_lines:
            puml_lines.append(f"note right")
            puml_lines.extend(note_lines)
            puml_lines.append("end note")
            
    puml_lines.append("@enduml")
    
    output_path = path.with_suffix('.puml')
    with open(output_path, 'w') as f:
        f.write("\n".join(puml_lines))
    
    print(f"Generated {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PlantUML from JSON test results")
    parser.add_argument("files", nargs='+', help="JSON files to process")
    args = parser.parse_args()
    
    for file in args.files:
        generate_puml(file)
