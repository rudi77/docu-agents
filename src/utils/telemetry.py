"""
OpenTelemetry setup and configuration for the document processing system.
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

from ..config.settings import settings

def setup_telemetry():
    """
    Initialize OpenTelemetry with basic configuration.
    Sets up a TracerProvider with console export for development.
    """
    # Create a resource with service name
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: settings.OTEL_SERVICE_NAME
    })
    
    # Initialize TracerProvider with the resource
    provider = TracerProvider(resource=resource)
    
    # Add console exporter for development
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    
    # Set the global TracerProvider
    trace.set_tracer_provider(provider)
    
    return trace.get_tracer(__name__)

# Create a global tracer instance
tracer = setup_telemetry() 