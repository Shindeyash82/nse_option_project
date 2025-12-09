"""
Short-lived in-memory loop keeping last-N snapshots in a deque.
Designed for real-time monitoring without disk persistence.
"""
import time
from collections import deque
from datetime import datetime
from typing import Optional, Dict, Any
from src.fetch_predict import OptionChainPredictor


class RealtimeMonitor:
    """In-memory real-time option chain monitor."""
    
    def __init__(self, max_snapshots: int = 100, symbol: str = "NIFTY", interval: float = 5.0):
        """
        Initialize real-time monitor.
        
        Args:
            max_snapshots: Maximum number of snapshots to keep in memory
            symbol: Option symbol to monitor
            interval: Fetch interval in seconds
        """
        self.max_snapshots = max_snapshots
        self.symbol = symbol
        self.interval = interval
        self.predictor = OptionChainPredictor()
        self.snapshots = deque(maxlen=max_snapshots)
        self.running = False
    
    def add_snapshot(self, snapshot: Dict[str, Any]):
        """Add a snapshot to the deque."""
        snapshot['timestamp'] = datetime.now().isoformat()
        self.snapshots.append(snapshot)
    
    def get_latest(self) -> Optional[Dict[str, Any]]:
        """Get the latest snapshot."""
        return self.snapshots[-1] if self.snapshots else None
    
    def get_recent(self, n: int = 10) -> list:
        """Get the last N snapshots."""
        return list(self.snapshots)[-n:]
    
    def get_all(self) -> list:
        """Get all snapshots."""
        return list(self.snapshots)
    
    def run_once(self) -> Optional[Dict[str, Any]]:
        """
        Fetch and predict once, add to snapshots.
        
        Returns:
            Snapshot dictionary or None if fetch fails
        """
        result = self.predictor.fetch_and_predict(self.symbol)
        if result:
            self.add_snapshot(result)
        return result
    
    def run(self, duration: Optional[float] = None):
        """
        Run continuous monitoring loop.
        
        Args:
            duration: Optional duration in seconds (None = run indefinitely)
        """
        self.running = True
        start_time = time.time()
        
        print(f"Starting real-time monitor for {self.symbol}")
        print(f"Interval: {self.interval}s, Max snapshots: {self.max_snapshots}")
        
        try:
            while self.running:
                if duration and (time.time() - start_time) > duration:
                    break
                
                snapshot = self.run_once()
                if snapshot:
                    print(f"[{datetime.now()}] Snapshot added: "
                          f"Predicted={snapshot.get('predicted_class', 'N/A')}, "
                          f"Spot={snapshot.get('spot', 'N/A')}")
                else:
                    print(f"[{datetime.now()}] Failed to fetch snapshot")
                
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            print("\nStopping monitor...")
        finally:
            self.running = False
            print(f"Monitor stopped. Total snapshots: {len(self.snapshots)}")
    
    def stop(self):
        """Stop the monitoring loop."""
        self.running = False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about collected snapshots."""
        if not self.snapshots:
            return {}
        
        predictions = [s.get('predicted_class_idx') for s in self.snapshots if 'predicted_class_idx' in s]
        spots = [s.get('spot') for s in self.snapshots if 'spot' in s]
        
        stats = {
            'total_snapshots': len(self.snapshots),
            'first_timestamp': self.snapshots[0].get('timestamp') if self.snapshots else None,
            'last_timestamp': self.snapshots[-1].get('timestamp') if self.snapshots else None,
        }
        
        if predictions:
            from collections import Counter
            stats['prediction_distribution'] = dict(Counter(predictions))
        
        if spots:
            stats['spot_min'] = min(spots)
            stats['spot_max'] = max(spots)
            stats['spot_mean'] = sum(spots) / len(spots)
        
        return stats


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Real-time option chain monitor")
    parser.add_argument("--symbol", default="NIFTY", help="Option symbol")
    parser.add_argument("--interval", type=float, default=5.0, help="Fetch interval in seconds")
    parser.add_argument("--max-snapshots", type=int, default=100, help="Maximum snapshots to keep")
    parser.add_argument("--duration", type=float, help="Run duration in seconds (default: indefinite)")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    monitor = RealtimeMonitor(
        max_snapshots=args.max_snapshots,
        symbol=args.symbol,
        interval=args.interval
    )
    
    if args.once:
        result = monitor.run_once()
        if result:
            import json
            print(json.dumps(result, indent=2))
    else:
        monitor.run(duration=args.duration)



