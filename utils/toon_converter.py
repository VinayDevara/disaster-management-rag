"""
TOON Format Converter
Converts JSON/CSV to TOON format for low-resource environments
"""

class TOONConverter:
    """
    TOON (Tiny Object Oriented Notation) Format Converter
    Optimized for low-resource edge devices
    """
    
    @staticmethod
    def dict_to_toon(data: dict, indent_level: int = 0) -> str:
        """Convert dictionary to TOON format"""
        indent = "  " * indent_level
        lines = []
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{indent}{key}:")
                lines.append(TOONConverter.dict_to_toon(value, indent_level + 1))
            elif isinstance(value, list):
                if len(value) == 0:
                    lines.append(f"{indent}{key}[0]:")
                elif isinstance(value[0], dict):
                    # List of objects with schema
                    schema_keys = list(value[0].keys())
                    lines.append(f"{indent}{key}[{len(value)}]{{{','.join(schema_keys)}}}:")
                    for i, item in enumerate(value, 1):
                        item_values = [str(item.get(k, '')) for k in schema_keys]
                        lines.append(f"{indent}  {i},{','.join(item_values)}")
                else:
                    # Simple list
                    lines.append(f"{indent}{key}[{len(value)}]:{','.join(map(str, value))}")
            else:
                lines.append(f"{indent}{key}: {value}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def list_to_toon(data: list, name: str = "items") -> str:
        """Convert list to TOON format"""
        if not data:
            return f"{name}[0]:"
        
        if isinstance(data[0], dict):
            schema_keys = list(data[0].keys())
            lines = [f"{name}[{len(data)}]{{{','.join(schema_keys)}}}:"]
            for i, item in enumerate(data, 1):
                item_values = [str(item.get(k, '')) for k in schema_keys]
                lines.append(f"  {i},{','.join(item_values)}")
            return '\n'.join(lines)
        else:
            return f"{name}[{len(data)}]:{','.join(map(str, data))}"
    
    @staticmethod
    def toon_to_dict(toon_str: str) -> dict:
        """Convert TOON format back to dictionary (basic parser)"""
        result = {}
        lines = toon_str.strip().split('\n')
        current_key = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if ':' in line and not line.startswith((' ', '\t')):
                parts = line.split(':', 1)
                key = parts[0].strip()
                value = parts[1].strip() if len(parts) > 1 else None
                
                # Handle list notation
                if '[' in key:
                    key_name = key.split('[')[0]
                    current_key = key_name
                    result[key_name] = []
                elif value:
                    result[key] = value
                else:
                    current_key = key
                    result[key] = {}
            elif current_key and ',' in line:
                # List item
                if isinstance(result[current_key], list):
                    result[current_key].append(line)
        
        return result
    
    @staticmethod
    def estimate_size_reduction(original_json: str, toon_str: str) -> dict:
        """Estimate size reduction percentage"""
        original_size = len(original_json.encode('utf-8'))
        toon_size = len(toon_str.encode('utf-8'))
        reduction = ((original_size - toon_size) / original_size) * 100
        
        return {
            'original_size_bytes': original_size,
            'toon_size_bytes': toon_size,
            'reduction_percent': round(reduction, 2),
            'compression_ratio': round(original_size / toon_size, 2) if toon_size > 0 else 0
        }


def convert_adsb_to_toon(adsb_data: dict) -> str:
    """
    Convert ADS-B aircraft data to TOON format
    Optimized for edge device storage
    """
    toon_output = f"""context:
  task: ADS-B Flight Tracking
  timestamp: {adsb_data.get('now', 'unknown')}
  total_messages: {adsb_data.get('messages', 0)}

"""
    
    aircraft_list = adsb_data.get('aircraft', [])
    if aircraft_list:
        # Extract schema from first aircraft
        schema_keys = ['hex', 'flight', 'alt_baro', 'gs', 'track', 'lat', 'lon', 'squawk', 'category']
        available_keys = [k for k in schema_keys if k in aircraft_list[0]]
        
        toon_output += f"aircraft[{len(aircraft_list)}]{{{','.join(available_keys)}}}:\n"
        
        for i, aircraft in enumerate(aircraft_list, 1):
            values = []
            for key in available_keys:
                val = aircraft.get(key, '')
                values.append(str(val) if val not in [None, ''] else 'N/A')
            toon_output += f"  {i},{','.join(values)}\n"
    
    return toon_output


if __name__ == "__main__":
    # Test TOON conversion
    test_data = {
        "context": {
            "task": "Flight tracking",
            "location": "Global"
        },
        "aircraft": [
            {"hex": "ABC123", "flight": "AA100", "altitude": 35000, "speed": 450},
            {"hex": "DEF456", "flight": "UA200", "altitude": 38000, "speed": 480}
        ]
    }
    
    toon = TOONConverter.dict_to_toon(test_data)
    print("TOON Format:")
    print(toon)
    print("\n" + "="*50)
    
    import json
    original_json = json.dumps(test_data, indent=2)
    stats = TOONConverter.estimate_size_reduction(original_json, toon)
    print(f"Size Reduction: {stats['reduction_percent']}%")
    print(f"Compression Ratio: {stats['compression_ratio']}x")
