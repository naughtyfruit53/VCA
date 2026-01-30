"""
Runtime Context Builder for Agent Brain v1 APIs.

IMPORTANT: This service assembles prompts but DOES NOT call any LLM.
All responses are clearly marked as simulated/mock.

The service builds runtime context from:
- Global rules
- Language-specific templates
- Business profile configuration
"""

from typing import Dict, Optional, List, Any


class RuntimeContextBuilder:
    """
    Runtime context builder for Agent Brain v1.
    
    This service assembles prompts from various configuration sources
    but DOES NOT make any LLM calls. It returns assembled text.
    
    Components assembled:
    - Global agent rules
    - Language-specific response templates
    - Business profile information (name, type, services, etc.)
    - Operating parameters (hours, booking, escalation)
    """
    
    def __init__(self):
        """Initialize the runtime context builder."""
        pass
    
    def build_context(
        self,
        business_profile: Optional[Dict[str, Any]],
        speaking_language: str = "en",
        user_text: Optional[str] = None
    ) -> str:
        """
        Assemble runtime context from configuration (NO LLM CALL).
        
        This method assembles a prompt from various configuration sources
        but does NOT call any LLM. It returns the assembled text.
        
        Args:
            business_profile: Business profile configuration dict
            speaking_language: Language code for response templates
            user_text: Optional user input text to include in context
            
        Returns:
            Assembled prompt text as string
            
        Note:
            This does NOT call any LLM. It only assembles configuration into text.
        """
        # Start building the context
        context_parts = []
        
        # Global rules section
        context_parts.append("=== GLOBAL AGENT RULES ===")
        context_parts.append(self._get_global_rules())
        context_parts.append("")
        
        # Language-specific templates
        context_parts.append(f"=== LANGUAGE TEMPLATE ({speaking_language.upper()}) ===")
        context_parts.append(self._get_language_template(speaking_language))
        context_parts.append("")
        
        # Business profile information
        if business_profile:
            context_parts.append("=== BUSINESS PROFILE ===")
            context_parts.append(self._format_business_profile(business_profile))
            context_parts.append("")
        
        # User input (if provided)
        if user_text:
            context_parts.append("=== USER INPUT ===")
            context_parts.append(user_text)
            context_parts.append("")
        
        # Assembly note
        context_parts.append("=== ASSEMBLY NOTE ===")
        context_parts.append("This context was assembled from configuration.")
        context_parts.append("NO AI inference has been performed.")
        
        return "\n".join(context_parts)
    
    def _get_global_rules(self) -> str:
        """
        Get global agent rules.
        
        These are universal rules that apply to all agents regardless of
        business profile or language.
        
        Returns:
            Global rules as text
        """
        rules = [
            "1. Always be polite and professional",
            "2. Never share customer data with third parties",
            "3. Escalate to human if unable to help",
            "4. Follow business-specific escalation rules",
            "5. Respect business hours and booking policies",
            "6. Never make forbidden statements",
        ]
        return "\n".join(rules)
    
    def _get_language_template(self, language: str) -> str:
        """
        Get language-specific response templates.
        
        These templates provide language-appropriate greeting and response patterns.
        
        Args:
            language: Language code (en/hi/mr/gu)
            
        Returns:
            Language template as text
        """
        templates = {
            "en": (
                "Greetings: Hello, Hi, Good morning/afternoon/evening\n"
                "Acknowledgment: I understand, Got it, Sure\n"
                "Questions: How can I help? What would you like to know?\n"
                "Closing: Thank you, Have a great day, Goodbye"
            ),
            "hi": (
                "Greetings: नमस्ते, नमस्कार\n"
                "Acknowledgment: मैं समझता हूं, ठीक है\n"
                "Questions: मैं आपकी कैसे मदद कर सकता हूं?\n"
                "Closing: धन्यवाद, शुभ दिन"
            ),
            "mr": (
                "Greetings: नमस्कार\n"
                "Acknowledgment: मला समजले, ठीक आहे\n"
                "Questions: मी तुमची कशी मदत करू शकतो?\n"
                "Closing: धन्यवाद, शुभ दिन"
            ),
            "gu": (
                "Greetings: નમસ્તે, નમસ્કાર\n"
                "Acknowledgment: હું સમજું છું, બરાબર\n"
                "Questions: હું તમને કેવી રીતે મદદ કરી શકું?\n"
                "Closing: આભાર, શુભ દિવસ"
            )
        }
        return templates.get(language, templates["en"])
    
    def _format_business_profile(self, profile: Dict[str, Any]) -> str:
        """
        Format business profile information into text.
        
        Args:
            profile: Business profile dict
            
        Returns:
            Formatted business profile as text
        """
        parts = []
        
        # Business identity
        if "business_name" in profile:
            parts.append(f"Business Name: {profile['business_name']}")
        if "business_type" in profile:
            parts.append(f"Business Type: {profile['business_type']}")
        
        # Services
        if "services" in profile and profile["services"]:
            services_str = ", ".join(profile["services"])
            parts.append(f"Services Offered: {services_str}")
        
        # Service areas
        if "service_areas" in profile and profile["service_areas"]:
            areas_str = ", ".join(profile["service_areas"])
            parts.append(f"Service Areas: {areas_str}")
        
        # Business hours
        if "business_hours" in profile and profile["business_hours"]:
            parts.append("Business Hours:")
            for day, hours in profile["business_hours"].items():
                parts.append(f"  {day}: {hours}")
        
        # Booking
        if "booking_enabled" in profile:
            status = "Enabled" if profile["booking_enabled"] else "Disabled"
            parts.append(f"Booking: {status}")
        
        # Escalation rules
        if "escalation_rules" in profile and profile["escalation_rules"]:
            parts.append("Escalation Rules:")
            for condition, action in profile["escalation_rules"].items():
                parts.append(f"  {condition}: {action}")
        
        # Forbidden statements
        if "forbidden_statements" in profile and profile["forbidden_statements"]:
            parts.append("Forbidden Statements:")
            for statement in profile["forbidden_statements"]:
                parts.append(f"  - {statement}")
        
        return "\n".join(parts)
