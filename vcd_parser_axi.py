"""
VCD Parser Tutorial for Beginners
A step-by-step guide to parsing VCD files and visualizing waveforms
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict

# ============================================================================
# STEP 1: Parse the VCD File
# ============================================================================

def parse_vcd(filename):
    """
    Parse a VCD file and extract signal definitions and value changes.
    
    Args:
        filename: Path to the VCD file
        
    Returns:
        signals: Dictionary mapping symbols to signal information
        timeline: Dictionary mapping timestamps to value changes
    """
    
    # These will store our parsed data
    signals = {}  # Maps symbol -> {name, width, type, values}
    timeline = defaultdict(list)  # Maps time -> list of changes
    
    current_time = 0
    in_definitions = True
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()  # Remove whitespace from start/end
            
            # ----------------------------------------------------------------
            # Parse signal definitions (the $var lines)
            # ----------------------------------------------------------------
            if line.startswith('$var'):
                # Example: $var reg 1 ! clk $end
                # Split into parts: ['$var', 'reg', '1', '!', 'clk', '$end']
                parts = line.split()
                
                signal_type = parts[1]   # 'reg' or 'wire'
                width = int(parts[2])    # Number of bits
                symbol = parts[3]        # The identifier (!, ", #, etc.)
                name = parts[4]          # The signal name (clk, reset, etc.)
                
                # Store signal info in our dictionary
                signals[symbol] = {
                    'name': name,
                    'width': width,
                    'type': signal_type,
                    'values': []  # Will store (time, value) tuples
                }
                
                print(f"Found signal: {name} (symbol: {symbol}, width: {width} bits)")
            
            # ----------------------------------------------------------------
            # Mark end of definitions section
            # ----------------------------------------------------------------
            if line.startswith('$enddefinitions'):
                in_definitions = False
                print("\n--- Starting to parse value changes ---\n")
            
            # ----------------------------------------------------------------
            # Parse timestamps (lines starting with #)
            # ----------------------------------------------------------------
            if line.startswith('#') and not in_definitions:
                # Example: #5000
                # Remove the # and convert to integer
                current_time = int(line[1:])
            
            # ----------------------------------------------------------------
            # Parse value changes
            # ----------------------------------------------------------------
            if not in_definitions and not line.startswith(('$', '#')) and line:
                symbol = None
                value = None
                
                # Case 1: Single-bit signals (0! or 1! or x!)
                if len(line) >= 2 and line[0] in '01xX':
                    value = line[0]
                    symbol = line[1:]
                
                # Case 2: Multi-bit signals (b1010 * or b0 ,)
                elif line.startswith('b'):
                    parts = line.split()
                    value = parts[0][1:]  # Remove 'b' prefix
                    symbol = parts[1] if len(parts) > 1 else None
                
                # Store the change if we found a valid symbol
                if symbol and symbol in signals:
                    signals[symbol]['values'].append((current_time, value))
                    timeline[current_time].append((symbol, value))
    
    print(f"\nParsing complete! Found {len(signals)} signals")
    print(f"Total time points: {len(timeline)}")
    
    return signals, timeline


# ============================================================================
# STEP 2: Analyze Signal Behavior
# ============================================================================

def analyze_signal(signal_data, signal_name):
    """
    Analyze a specific signal's behavior.
    
    Args:
        signal_data: The signal dictionary from parse_vcd
        signal_name: Name of the signal to analyze
    """
    # Find the signal by name
    signal_info = None
    for symbol, info in signal_data.items():
        if info['name'] == signal_name:
            signal_info = info
            break
    
    if not signal_info:
        print(f"Signal '{signal_name}' not found!")
        return
    
    print(f"\n=== Analysis of '{signal_name}' ===")
    print(f"Type: {signal_info['type']}")
    print(f"Width: {signal_info['width']} bit(s)")
    print(f"Number of transitions: {len(signal_info['values'])}")
    
    # Show first few transitions
    print(f"\nFirst 10 value changes:")
    for i, (time, value) in enumerate(signal_info['values'][:10]):
        print(f"  Time {time:6d} ps: {value}")
    
    # If it's a clock signal, calculate frequency
    if 'clk' in signal_name.lower() and len(signal_info['values']) >= 3:
        # Find time between two rising edges
        rising_edges = [t for t, v in signal_info['values'] if v == '1']
        if len(rising_edges) >= 2:
            period = rising_edges[1] - rising_edges[0]
            frequency_mhz = 1e6 / period  # Convert ps to MHz
            print(f"\nClock period: {period} ps")
            print(f"Clock frequency: {frequency_mhz:.2f} MHz")


# ============================================================================
# STEP 3: Visualize Waveforms
# ============================================================================

def plot_waveforms(signals, signal_names, max_time=None):
    """
    Plot digital waveforms for specified signals.
    
    Args:
        signals: The signals dictionary from parse_vcd
        signal_names: List of signal names to plot
        max_time: Maximum time to display (None = all)
    """
    num_signals = len(signal_names)
    fig, axes = plt.subplots(num_signals, 1, figsize=(14, 2*num_signals), sharex=True)
    
    # Handle case of single signal
    if num_signals == 1:
        axes = [axes]
    
    for idx, signal_name in enumerate(signal_names):
        ax = axes[idx]
        
        # Find signal data
        signal_info = None
        for symbol, info in signals.items():
            if info['name'] == signal_name:
                signal_info = info
                break
        
        if not signal_info:
            continue
        
        # Extract times and values
        times = []
        values = []
        
        for time, value in signal_info['values']:
            if max_time and time > max_time:
                break
            times.append(time)
            # Convert binary string to integer for multi-bit signals
            if signal_info['width'] > 1:
                try:
                    values.append(int(value, 2))
                except:
                    values.append(0)  # Handle 'x' or invalid values
            else:
                values.append(1 if value == '1' else 0)
        
        # Create step plot
        if signal_info['width'] == 1:
            # Binary signal - use step plot
            for i in range(len(times) - 1):
                ax.hlines(values[i], times[i], times[i+1], colors='green', linewidth=2)
                ax.vlines(times[i+1], values[i], values[i+1], colors='green', linewidth=2)
            ax.set_ylim(-0.2, 1.2)
            ax.set_yticks([0, 1])
        else:
            # Multi-bit signal - use step plot with actual values
            ax.step(times, values, where='post', linewidth=2, color='blue')
            ax.set_ylabel('Value')
        
        ax.set_title(f"{signal_name} ({signal_info['width']} bit)", fontsize=10, loc='left')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(left=0)
    
    axes[-1].set_xlabel('Time (ps)')
    plt.tight_layout()
    plt.savefig('waveforms.png', dpi=150, bbox_inches='tight')
    print("\nWaveform plot saved as 'waveforms.png'")
    plt.show()


# ============================================================================
# STEP 4: Main Program - Put it all together!
# ============================================================================

def main():
    """
    Main program to parse VCD and analyze signals.
    """
    print("=" * 60)
    print("VCD Parser Tutorial")
    print("=" * 60)
    
    # Parse the VCD file
    vcd_file = 'test.vcd'  # Change this to your file path
    signals, timeline = parse_vcd(vcd_file)

    # Print all available signal names
    print("\n" + "=" * 60)
    print("ALL AVAILABLE SIGNALS:")
    print("=" * 60)
    for symbol, info in signals.items():
        print(f"{info['name']}")
    print("=" * 60)
    
    # Analyze specific signals
    print("\n" + "=" * 60)
    print("Signal Analysis")
    print("=" * 60)
    
    analyze_signal(signals, 'clk')
    analyze_signal(signals, 'm_data')
    analyze_signal(signals, 'm_valid')
    analyze_signal(signals, 'm_ready')
    
    # Plot waveforms
    print("\n" + "=" * 60)
    print("Generating Waveform Plots")
    print("=" * 60)
    
    # Plot CLK with the two AXI signals
    signals_to_plot = ['clk', 'm_data', 'm_valid', 'm_ready']
    
    plot_waveforms(signals, signals_to_plot, max_time=100000)  # First 100ns
    
    print("\nDone! Check the output plot.")


# ============================================================================
# Run the program
# ============================================================================

if __name__ == "__main__":
    main()
