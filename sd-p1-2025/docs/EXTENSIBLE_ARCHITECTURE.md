# EV Charging Point - Extensible Architecture with Kafka Integration

## Overview

The EV Charging Point system has been enhanced with an extensible architecture that supports:
- **Kafka integration** for real-time messaging
- **Pluggable message handlers** for different message types  
- **Extensible monitoring** with multiple reporting mechanisms
- **Backward compatibility** with existing Central server communication

## Architecture Components

### 1. EV_CP_E (Charging Point Engine)
The engine now includes:
- **KafkaConsumerService**: Extensible message consumer with handler registration
- **MessageHandler base class**: Abstract base for creating custom message processors
- **Pre-built handlers**: UserInfoHandler, ChargingRequestHandler, SystemNotificationHandler
- **Automatic retry logic**: Handles Kafka connection failures gracefully

#### Adding Custom Message Handlers

```python
class CustomMessageHandler(MessageHandler):
    def can_handle(self, message: Dict[str, Any]) -> bool:
        return message.get("kind") == "CUSTOM_MESSAGE"
    
    def handle(self, message: Dict[str, Any]) -> None:
        # Your custom logic here
        print(f"Processing custom message: {message}")

# Register the handler
kafka_service.register_handler(CustomMessageHandler())
```

#### Kafka Message Format
Messages should follow this JSON structure:
```json
{
    "kind": "USER_INFO|CHARGING_REQUEST|SYSTEM_NOTIFICATION|CUSTOM_MESSAGE",
    "timestamp": "ISO timestamp",
    "data": { /* message-specific data */ }
}
```

### 2. EV_CP_M (Charging Point Monitor)
Enhanced monitoring includes:
- **MonitoringService**: Extensible monitoring with multiple output channels
- **Kafka producer**: Publishes detailed monitoring events
- **Callback system**: Register custom functions for status changes
- **Metrics tracking**: Detailed performance and availability metrics

#### Adding Custom Monitoring Callbacks

```python
def alert_callback(status_data: Dict[str, Any]):
    if status_data["status"] == "KO":
        # Send alert to external system
        send_alert(f"CP {status_data['id']} is down!")

monitoring_service.register_callback(alert_callback)
```

## Kafka Topics

- **user_messages**: User information and requests
- **charging_requests**: Charging session requests
- **system_notifications**: System-wide notifications
- **monitoring_events**: Health and performance metrics

## Configuration

### Environment Variables
```bash
# Kafka Configuration
KAFKA_BROKERS=kafka:9092
KAFKA_TOPICS=user_messages,charging_requests,system_notifications
KAFKA_GROUP_ID=cp_engine_CP-001

# Charging Point Configuration  
CP_ID=CP-001
CENTRAL_HOST=central
CENTRAL_PORT=9092
```

### Docker Deployment
```bash
# Start the complete system with Kafka
cd docker
docker-compose up -d

# View logs
docker-compose logs -f cp_engine_1
docker-compose logs -f cp_monitor_1

# Access Kafka UI (optional)
# http://localhost:8080
```

## Development Workflow

### 1. Running Locally
```bash
# Install dependencies
pipenv install

# Start individual components
pipenv run python src/EV_CP_E/EV_CP_E.py
pipenv run python src/EV_CP_M/EV_CP_M.py
```

### 2. Testing Kafka Integration
```python
# Send test message to Kafka
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:29092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send user info message
producer.send('user_messages', {
    'kind': 'USER_INFO',
    'user_id': 'user123',
    'data': {'name': 'John Doe', 'vehicle': 'Tesla Model 3'}
})

# Send charging request
producer.send('charging_requests', {
    'kind': 'CHARGING_REQUEST',
    'user_id': 'user123',
    'cp_id': 'CP-001',
    'requested_power': 50,
    'max_duration': 3600
})
```

## Extensibility Features

### Message Handler Registration
- Handlers can be registered/unregistered at runtime
- Support for dynamic message routing based on message content
- Error isolation - one handler failure doesn't affect others

### Monitoring Callbacks
- Multiple monitoring outputs (Central, Kafka, custom callbacks)
- Detailed metrics collection with timestamps
- Configurable alerting thresholds

### Protocol Compatibility
- Maintains backward compatibility with existing socket-based communication
- Gradual migration path to Kafka-based messaging
- Fallback mechanisms when Kafka is unavailable

## Error Handling

- **Graceful degradation**: System continues operating if Kafka is unavailable
- **Automatic retry**: Failed Kafka connections are retried periodically
- **Isolation**: Message handler errors don't crash the entire system
- **Logging**: Comprehensive logging for debugging and monitoring

## Future Extensions

The architecture supports easy addition of:
- New message types and handlers
- Additional monitoring outputs (metrics databases, alerting systems)
- Protocol adapters for different communication methods
- Load balancing and high availability features