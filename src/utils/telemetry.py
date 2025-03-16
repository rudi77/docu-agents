"""
OpenTelemetry setup and configuration for the document processing system.
"""
import logging
import base64
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

from ..config.settings import settings

logger = logging.getLogger(__name__)

def setup_telemetry():
    """
    Initialize OpenTelemetry with Langfuse integration.
    Sets up a TracerProvider with OTLP export for Langfuse.
    """
    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry is disabled. Skipping setup.")
        return None

    try:
        # Create a resource with service name
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: settings.OTEL_SERVICE_NAME
        })
        
        # Initialize TracerProvider with the resource
        provider = TracerProvider(resource=resource)
        
        # Add OTLP exporter for Langfuse
        if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
            processor = SimpleSpanProcessor(OTLPSpanExporter())
            provider.add_span_processor(processor)
            logger.info("Added OTLP exporter for Langfuse")
        else:
            logger.warning("OTEL_EXPORTER_OTLP_ENDPOINT not set. No traces will be exported.")
        
        # Set the global TracerProvider
        trace.set_tracer_provider(provider)
        
        # Instrument smolagents
        SmolagentsInstrumentor().instrument(tracer_provider=provider)
        
        logger.info("OpenTelemetry setup completed successfully")
        return trace.get_tracer(__name__)
        
    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry: {e}")
        return None

# Create a global tracer instance
tracer = setup_telemetry()
