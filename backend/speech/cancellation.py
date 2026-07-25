class CancellationToken:
    """Correlation token signaling task cancellations across threads/coroutines."""
    
    def __init__(self) -> None:
        self._is_cancelled: bool = False

    @property
    def is_cancelled(self) -> bool:
        """Returns True if the task has been cancelled."""
        return self._is_cancelled

    def cancel(self) -> None:
        """Triggers the cancellation flag."""
        self._is_cancelled = True

    def raise_if_cancelled(self) -> None:
        """Raises a RuntimeError if the cancellation flag is active.
        
        Raises:
            RuntimeError: Signaling task execution was cancelled.
        """
        if self._is_cancelled:
            raise RuntimeError("Task execution was cancelled by the user.")
