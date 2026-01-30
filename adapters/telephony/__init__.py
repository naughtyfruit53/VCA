"""
Telephony adapters package.

This package contains telephony provider adapters for inbound call handling.
"""

from .InboundTelephonyAdapter import ExotelInboundAdapter

__all__ = ['ExotelInboundAdapter']
