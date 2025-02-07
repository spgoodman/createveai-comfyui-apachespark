"""
UI utilities for ComfyUI integration
"""

from typing import Optional, Dict, Any, Callable
import time
from dataclasses import dataclass
from enum import Enum

class ProgressState(Enum):
    """Progress states for node execution"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class ProgressInfo:
    """Progress information for node execution"""
    state: ProgressState
    value: float  # 0-1
    text: str
    error_message: Optional[str] = None

class ProgressTracker:
    """Track progress of node operations"""
    
    def __init__(self):
        self._progress: Dict[str, ProgressInfo] = {}
        self._start_times: Dict[str, float] = {}
    
    def start_operation(self, operation_id: str, text: str = "Starting..."):
        """Start tracking an operation"""
        self._progress[operation_id] = ProgressInfo(
            state=ProgressState.RUNNING,
            value=0.0,
            text=text
        )
        self._start_times[operation_id] = time.time()
    
    def update_progress(self, 
                       operation_id: str, 
                       value: float,
                       text: Optional[str] = None):
        """Update operation progress"""
        if operation_id not in self._progress:
            return
        
        progress = self._progress[operation_id]
        progress.value = max(0.0, min(1.0, value))
        if text:
            progress.text = text
    
    def complete_operation(self, operation_id: str, text: str = "Completed"):
        """Mark operation as completed"""
        if operation_id in self._progress:
            self._progress[operation_id] = ProgressInfo(
                state=ProgressState.COMPLETED,
                value=1.0,
                text=text
            )
    
    def error_operation(self, 
                       operation_id: str, 
                       error_message: str,
                       text: str = "Error"):
        """Mark operation as failed"""
        if operation_id in self._progress:
            self._progress[operation_id] = ProgressInfo(
                state=ProgressState.ERROR,
                value=0.0,
                text=text,
                error_message=error_message
            )
    
    def get_progress(self, operation_id: str) -> Optional[ProgressInfo]:
        """Get current progress of operation"""
        return self._progress.get(operation_id)
    
    def clear_operation(self, operation_id: str):
        """Clear operation tracking"""
        self._progress.pop(operation_id, None)
        self._start_times.pop(operation_id, None)
    
    def get_elapsed_time(self, operation_id: str) -> Optional[float]:
        """Get elapsed time for operation in seconds"""
        if operation_id in self._start_times:
            return time.time() - self._start_times[operation_id]
        return None

class NodeWidgetMixin:
    """Mixin for adding widget support to nodes"""
    
    @classmethod
    def add_widget(cls,
                  name: str,
                  widget_type: str,
                  default: Any = None,
                  options: Optional[Dict] = None) -> Dict:
        """Add a widget configuration"""
        widget = {
            "name": name,
            "type": widget_type,
            "default": default
        }
        if options:
            widget.update(options)
        return widget
    
    @classmethod
    def add_combo_widget(cls,
                        name: str,
                        choices: list,
                        default: Any = None,
                        options: Optional[Dict] = None) -> Dict:
        """Add a combo box widget"""
        return cls.add_widget(
            name=name,
            widget_type="combo",
            default=default or choices[0],
            options={"choices": choices, **(options or {})}
        )
    
    @classmethod
    def add_text_widget(cls,
                       name: str,
                       default: str = "",
                       multiline: bool = False,
                       options: Optional[Dict] = None) -> Dict:
        """Add a text input widget"""
        return cls.add_widget(
            name=name,
            widget_type="text",
            default=default,
            options={"multiline": multiline, **(options or {})}
        )
    
    @classmethod
    def add_number_widget(cls,
                         name: str,
                         default: float = 0.0,
                         min_value: Optional[float] = None,
                         max_value: Optional[float] = None,
                         step: Optional[float] = None,
                         options: Optional[Dict] = None) -> Dict:
        """Add a number input widget"""
        widget_opts = {}
        if min_value is not None:
            widget_opts["min"] = min_value
        if max_value is not None:
            widget_opts["max"] = max_value
        if step is not None:
            widget_opts["step"] = step
        if options:
            widget_opts.update(options)
            
        return cls.add_widget(
            name=name,
            widget_type="number",
            default=default,
            options=widget_opts
        )

def with_progress(operation_id: str) -> Callable:
    """Decorator for tracking progress of node operations"""
    def decorator(func: Callable) -> Callable:
        def wrapper(self, *args, **kwargs):
            tracker = getattr(self, "_progress_tracker", None)
            if not tracker:
                tracker = ProgressTracker()
                setattr(self, "_progress_tracker", tracker)
            
            try:
                tracker.start_operation(operation_id)
                result = func(self, *args, **kwargs)
                tracker.complete_operation(operation_id)
                return result
            except Exception as e:
                tracker.error_operation(operation_id, str(e))
                raise
            finally:
                tracker.clear_operation(operation_id)
        return wrapper
    return decorator
