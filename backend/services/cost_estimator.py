from typing import Dict, Optional
from pydantic import BaseModel, Field

class ModelPricing(BaseModel):
    """Rates mapping cost per 1,000 tokens for prompt inputs and completions output."""
    prompt_rate_per_1k: float = Field(default=0.0, description="Cost rate per 1,000 prompt tokens")
    completion_rate_per_1k: float = Field(default=0.0, description="Cost rate per 1,000 completion tokens")


class CostEstimation(BaseModel):
    """Cost breakdown for a completed AI generation task."""
    prompt_cost: float = Field(default=0.0, description="Cost of input prompt tokens")
    completion_cost: float = Field(default=0.0, description="Cost of output completion tokens")
    total_cost: float = Field(default=0.0, description="Sum total of input and output costs")


class CostEstimator:
    """Calculates completion expenses based on model rates mappings."""
    
    def __init__(self, pricing_dict: Optional[Dict[str, ModelPricing]] = None) -> None:
        # Default pricing models setup
        self._pricing: Dict[str, ModelPricing] = pricing_dict or {
            "gpt-3.5-turbo": ModelPricing(prompt_rate_per_1k=0.0015, completion_rate_per_1k=0.002),
            "gpt-4": ModelPricing(prompt_rate_per_1k=0.03, completion_rate_per_1k=0.06),
            "gpt-4o-mini": ModelPricing(prompt_rate_per_1k=0.00015, completion_rate_per_1k=0.0006)
        }

    def update_pricing(self, model_name: str, pricing: ModelPricing) -> None:
        """Configures or updates rate schemas for a model.
        
        Args:
            model_name (str): Target model name.
            pricing (ModelPricing): Input/output rates configuration.
        """
        self._pricing[model_name] = pricing

    def estimate_cost(self, model_name: str, prompt_tokens: int, completion_tokens: int) -> CostEstimation:
        """Calculates estimated prompt, completion, and total costs.
        
        Args:
            model_name (str): The active model identifier.
            prompt_tokens (int): Count of input tokens.
            completion_tokens (int): Count of generated output tokens.
            
        Returns:
            CostEstimation: Financial breakdown values.
        """
        pricing = self._pricing.get(model_name, ModelPricing(prompt_rate_per_1k=0.0, completion_rate_per_1k=0.0))
        
        prompt_cost = (prompt_tokens / 1000.0) * pricing.prompt_rate_per_1k
        completion_cost = (completion_tokens / 1000.0) * pricing.completion_rate_per_1k
        total_cost = prompt_cost + completion_cost
        
        return CostEstimation(
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=total_cost
        )
