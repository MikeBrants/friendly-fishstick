"""
Monitor Python processes and their resource usage.
Can be run standalone or imported into Streamlit dashboard.
"""
import psutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json


def get_python_processes() -> List[Dict]:
    """Get all Python processes with their resource usage."""
    processes = []
    current_pid = psutil.Process().pid  # PID of current process
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 
                                     'memory_info', 'create_time', 'status']):
        try:
            # Check if it's a Python process
            if not proc.info['name'] or 'python' not in proc.info['name'].lower():
                continue
            
            cmdline = proc.info['cmdline'] or []
            cmdline_str = ' '.join(cmdline).lower()
            
            # Skip current process (monitor itself)
            if proc.info['pid'] == current_pid:
                continue
            
            # Skip Streamlit server process itself (the one running "streamlit run")
            # But keep processes that execute Python scripts (like app.py)
            cmdline_str = ' '.join(cmdline).lower()
            
            # Check if this is the Streamlit server launcher (not a script executor)
            # Pattern: python.exe ... streamlit.exe run app.py
            # We want to EXCLUDE the launcher but INCLUDE the script executor
            is_streamlit_launcher = False
            
            # Look for streamlit.exe or -m streamlit followed by 'run'
            for i, arg in enumerate(cmdline):
                arg_lower = arg.lower()
                if 'streamlit' in arg_lower:
                    # Check if next arg is 'run'
                    if i + 1 < len(cmdline) and cmdline[i + 1].lower() == 'run':
                        # This is the launcher - exclude it
                        is_streamlit_launcher = True
                        break
                    # Check if previous arg was -m (module mode)
                    if i > 0 and cmdline[i-1] == '-m' and i + 1 < len(cmdline) and cmdline[i + 1].lower() == 'run':
                        is_streamlit_launcher = True
                        break
            
            # Only exclude if it's the launcher AND doesn't have a .py script being executed
            # If it has a .py script, it's the executor process and we want to keep it
            has_py_script = any(arg.endswith('.py') for arg in cmdline)
            
            if is_streamlit_launcher and not has_py_script:
                continue
            
            # Extract script name - try multiple methods
            script_name = "Python Process"
            
            # Method 1: Look for .py files in cmdline
            for arg in cmdline:
                if arg.endswith('.py'):
                    arg_lower = arg.lower()
                    # Only skip the actual monitor_processes.py script, not test scripts
                    if 'monitor_processes.py' in arg_lower:
                        script_name = None
                        break
                    script_name = Path(arg).name
                    break
            
            # Method 2: If no .py found, use module name (e.g., -m streamlit)
            if script_name == "Python Process":
                for i, arg in enumerate(cmdline):
                    if arg == '-m' and i + 1 < len(cmdline):
                        module_name = cmdline[i+1]
                        # Skip streamlit module itself
                        if 'streamlit' in module_name.lower():
                            script_name = None
                            break
                        script_name = f"module: {module_name}"
                        break
            
            # Method 3: Use first non-python argument as identifier
            if script_name == "Python Process":
                for arg in cmdline[1:]:  # Skip python.exe
                    if not arg.startswith('-') and 'python' not in arg.lower():
                        script_name = Path(arg).name if '/' in arg or '\\' in arg else arg
                        break
            
            # Skip if we determined this should be excluded
            if script_name is None:
                continue
            
            # Get CPU percent (need to call it once for accurate reading)
            try:
                cpu_percent = proc.cpu_percent(interval=0.1)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                cpu_percent = 0.0
            
            # Get memory in MB
            memory_mb = proc.info['memory_info'].rss / (1024 * 1024)
            
            # Calculate runtime
            create_time = proc.info['create_time']
            runtime_seconds = time.time() - create_time
            runtime_str = format_runtime(runtime_seconds)
            
            processes.append({
                'pid': proc.info['pid'],
                'script': script_name,
                'cmdline': ' '.join(cmdline[:4]) + ('...' if len(cmdline) > 4 else ''),
                'cpu_percent': cpu_percent,
                'memory_mb': round(memory_mb, 1),
                'runtime': runtime_str,
                'status': proc.info['status'],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    # Sort by CPU usage (descending)
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    return processes


def format_runtime(seconds: float) -> str:
    """Format runtime in human-readable format."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def get_system_stats() -> Dict:
    """Get overall system statistics."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu_percent': cpu_percent,
        'cpu_count': psutil.cpu_count(),
        'memory_total_gb': round(memory.total / (1024**3), 1),
        'memory_used_gb': round(memory.used / (1024**3), 1),
        'memory_percent': memory.percent,
        'disk_total_gb': round(disk.total / (1024**3), 1),
        'disk_used_gb': round(disk.used / (1024**3), 1),
        'disk_percent': round((disk.used / disk.total) * 100, 1),
    }


def monitor_loop(interval: int = 2, output_file: Optional[Path] = None):
    """Continuously monitor processes and optionally save to file."""
    print("🔍 Monitoring Python processes... (Ctrl+C to stop)")
    print("-" * 80)
    
    try:
        while True:
            # Clear screen (works on Windows and Unix)
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Get data
            processes = get_python_processes()
            system = get_system_stats()
            
            # Print header
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n📊 System Monitor - {timestamp}")
            print("=" * 80)
            
            # System stats
            print(f"\n💻 System Resources:")
            print(f"  CPU: {system['cpu_percent']:.1f}% ({system['cpu_count']} cores)")
            print(f"  RAM: {system['memory_used_gb']:.1f}GB / {system['memory_total_gb']:.1f}GB ({system['memory_percent']:.1f}%)")
            print(f"  Disk: {system['disk_used_gb']:.1f}GB / {system['disk_total_gb']:.1f}GB ({system['disk_percent']:.1f}%)")
            
            # Processes
            print(f"\n🐍 Python Processes ({len(processes)}):")
            print("-" * 80)
            print(f"{'PID':<8} {'Script':<25} {'CPU%':<8} {'Memory (MB)':<12} {'Runtime':<12} {'Status':<10}")
            print("-" * 80)
            
            if not processes:
                print("  No Python processes found (excluding monitor/streamlit)")
            else:
                for proc in processes[:20]:  # Show top 20
                    print(f"{proc['pid']:<8} {proc['script']:<25} {proc['cpu_percent']:<8.1f} "
                          f"{proc['memory_mb']:<12.1f} {proc['runtime']:<12} {proc['status']:<10}")
            
            # Save to file if requested
            if output_file:
                data = {
                    'timestamp': timestamp,
                    'system': system,
                    'processes': processes,
                }
                output_file.write_text(json.dumps(data, indent=2))
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor Python processes")
    parser.add_argument("--interval", type=int, default=2, help="Update interval in seconds")
    parser.add_argument("--output", type=Path, help="Optional JSON output file")
    args = parser.parse_args()
    
    monitor_loop(interval=args.interval, output_file=args.output)
