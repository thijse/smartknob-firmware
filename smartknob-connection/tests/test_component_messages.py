#!/usr/bin/env python3
"""
Test script to verify new component messages are available
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartknob.proto_gen import smartknob_pb2

def test_component_messages():
    """Test that new component messages are available."""
    print("🧪 Testing new component message types...")
    
    # Test creating ToSmartknob with app_component
    message = smartknob_pb2.ToSmartknob()
    message.protocol_version = 1
    message.nonce = 123
    
    # Test AppComponent creation
    component = message.app_component
    component.component_id = "test_light"
    component.type = smartknob_pb2.ComponentType.TOGGLE
    component.display_name = "Test Light Switch"
    
    # Test ToggleConfig creation
    toggle_config = component.toggle
    toggle_config.off_label = "Off"
    toggle_config.on_label = "On"
    toggle_config.snap_point = 0.6
    toggle_config.snap_point_bias = -0.2
    toggle_config.detent_strength_unit = 0.8
    toggle_config.off_led_hue = 0    # Red
    toggle_config.on_led_hue = 120   # Green
    toggle_config.initial_state = False
    
    print("✅ ToSmartknob message created successfully")
    print(f"   Component ID: {component.component_id}")
    print(f"   Type: {smartknob_pb2.ComponentType.Name(component.type)}")
    print(f"   Display Name: {component.display_name}")
    print(f"   Toggle Off Label: {toggle_config.off_label}")
    print(f"   Toggle On Label: {toggle_config.on_label}")
    print(f"   Snap Point: {toggle_config.snap_point}")
    print(f"   Snap Point Bias: {toggle_config.snap_point_bias}")
    print(f"   Off LED Hue: {toggle_config.off_led_hue}")
    print(f"   On LED Hue: {toggle_config.on_led_hue}")
    
    # Test serialization
    serialized = message.SerializeToString()
    print(f"✅ Message serialized successfully ({len(serialized)} bytes)")
    
    # Test deserialization
    deserialized = smartknob_pb2.ToSmartknob()
    deserialized.ParseFromString(serialized)
    print("✅ Message deserialized successfully")
    print(f"   Deserialized Component ID: {deserialized.app_component.component_id}")
    
    return True

def test_component_types():
    """Test ComponentType enum values."""
    print("\n🔢 Testing ComponentType enum...")
    
    # Test enum values
    toggle_value = smartknob_pb2.ComponentType.TOGGLE
    print(f"✅ ComponentType.TOGGLE = {toggle_value}")
    
    # Test enum name lookup
    toggle_name = smartknob_pb2.ComponentType.Name(toggle_value)
    print(f"✅ ComponentType name lookup: {toggle_name}")
    
    return True

if __name__ == "__main__":
    print("🎯 SmartKnob Component Message Test")
    print("=" * 40)
    
    try:
        test_component_messages()
        test_component_types()
        print("\n🎉 All tests passed! Component messages are working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
