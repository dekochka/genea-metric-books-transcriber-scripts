"""
Base Step Class

Abstract base class for all wizard steps.
Defines the interface that all steps must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class WizardStep(ABC):
    """Base class for wizard steps."""
    
    def __init__(self, controller):
        """
        Initialize wizard step.
        
        Args:
            controller: WizardController instance for accessing shared data
        """
        self.controller = controller
    
    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """
        Execute the step and collect user input.
        
        Returns:
            Dictionary of collected data
        """
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate collected data.
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        pass
