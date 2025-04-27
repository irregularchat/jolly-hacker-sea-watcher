# jolly-hacker-sea-watcher
![static_media](/static_media/sea_watch-logo.png)

## Sighting Enrichment System

This system processes sighting data through a workflow that enriches it with AIS data and trust scores. It exposes metrics at two points:
1. When the ship sighting is first submitted
2. After enrichment is complete

### Prerequisites

- Python 3.9+
- Temporal CLI
- Virtual environment (recommended)

### Setup

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the System

The system can be started using the provided script:

```bash
# Make the script executable
chmod +x start_ship_enrichment.sh

# Start all components
./start_ship_enrichment.sh start

# Stop all components
./start_ship_enrichment.sh stop

# Restart all components
./start_ship_enrichment.sh restart
```

The script will:
1. Check for prerequisites (Python 3.9+, Temporal CLI)
2. Start the Temporal server
3. Start the AIS mock server
4. Start the Temporal worker
5. Start the main server

You can press Ctrl+C to stop all components when the script is running.

### Testing the System

1. Submit a ship sighting:
```bash
curl -X POST "http://localhost:8001/submit_ship" \
  -H "Content-Type: application/json" \
  -d '{
    "source_account_id": "test-account-1",
    "timestamp": "2024-04-27T00:00:00Z",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "picture_url": "https://example.com/ship1.jpg"
  }'
```

2. Check metrics:
```bash
curl http://localhost:8001/metrics
```

### Troubleshooting

If you encounter port conflicts:
```bash
# Kill all Python processes
pkill -f python

# Kill Temporal server
pkill -f temporal
```

### Metrics Format

The system exposes two types of metrics:

1. Initial metrics (when ship is submitted):
```
ship_info{source_account_id="test-account-1",latitude="37.7749",longitude="-122.4194",stage="initial"} 1
```

2. Final metrics (after enrichment):
```
ship_trust_score{source_account_id="test-account-1",latitude="37.7749",longitude="-122.4194",ais_number="AIS-12345",stage="final",enriched="true"} 0.85
ship_ais_number_total{source_account_id="test-account-1",latitude="37.7749",longitude="-122.4194",stage="final",enriched="true"} 1
```

### Architecture

```
Client -> FastAPI (/submit_ship) -> Temporal Server -> Worker -> Activities -> Enriched Data
                                                      |
                                                      v
                                               Metrics Storage
                                                      |
                                                      v
                                               FastAPI (/metrics)
```

- The FastAPI server handles ship submissions and metrics exposure
- Temporal handles the workflow execution
- The worker processes the enrichment activities
- Metrics are stored in memory and exposed via the /metrics endpoint

## Problem Statement

Maritime security forces and coastal communities in countries impacted by Chinese greyzone activities currently lack an integrated, real-time capability to detect, visualize, and respond to malign maritime activities—such as illegal fishing, automatic identification system (AIS) spoofing, misuse of maritime emergency laws, and unauthorized transshipments—conducted by foreign vessels exploiting regional vulnerabilities, particularly those flagged under convenience registries. The absence of a unified, intuitive system that combines multiple publicly available information (PAI) and commercial available information (CAI) —including AIS, radar, ELINT, and satellite imagery—limits the ability of local stakeholders to rapidly identify and mitigate threats. Additionally, low technical proficiency among regional maritime personnel and local fishermen requires solutions that offer simplified visualization, natural-language threat interpretation, and actionable, automated alerts. Building an accessible, crowdsourced platform that consolidates complex maritime data, detects anomalous vessel behavior, and communicates threats clearly and promptly can empower maritime authorities and affected communities to effectively counteract and disrupt these illicit maritime activities.

**** Look at insurance data for sources
**** 12 nautical miles (law of the sea), what is the delta between this range and the conntection . 
transperency increases security and accountability. 

## Solution Overview

### Edge Reporting

#### Mobile App (Priority)
- **Platform:** Android (primary), iOS (secondary)
- **Features:**
  - Geolocation-based incident reporting
  - Photo/video capture and upload
  - Automatic metadata collection (GPS coordinates, timestamp, sensor data)
  - Simple, intuitive UI for low-technical-literacy users
  - Offline capability with automatic data synchronization when online

#### WhatsApp Reporting (Secondary)
- **Features:**
  - Basic reporting using structured WhatsApp messages (predefined message format)
  - Requires minimal user input (incident type, vessel ID, basic description)
  - WhatsApp gateway parsing for automatic ingestion into the cloud database
  - Matrix bridge integration to process data and automate responses. 

#### SMS Reporting (Tertiary)
- **Features:**
  - Basic reporting using structured SMS (predefined message format)
  - Requires minimal user input (incident type, vessel ID, basic description)
  - SMS gateway parsing for automatic ingestion into the cloud database

#### Web Reporting (Option)
- **Platform:** Responsive web interface
- **Features:**
  - Simplified online form
  - Manual data entry with optional geolocation support
  - Multimedia attachment support (optional, dependent on bandwidth)

---

### Cloud Processing

#### Data Processing
- Automatic ingestion of reported data from all edge sources (app, SMS, web)
- Parsing structured and unstructured data
- Data normalization and sanitization to maintain user anonymity

#### Data Enrichment
- Integration with multiple PAI and CAI sources (AIS, satellite imagery, radar, ELINT)
- Cross-validation with third-party maritime databases
- Enrichment with historical vessel activity and behavior patterns

#### Data Validation
- Anomaly detection (AIS spoofing, irregular vessel movements, unauthorized transshipments)
- Machine learning algorithms to assess data credibility and identify suspicious patterns
- Human-in-the-loop verification process for high-priority alerts

#### Data Analysis
- AI-driven identification of vessel anomalies
- Real-time threat assessment based on aggregated and historical data
- Visualization of hotspots, risk areas, and vessel behavior anomalies

---

### Query Interface

#### Visualization and Data Exploration
- Interactive map interface displaying vessel positions, reported incidents, and hotspot areas
- Timeline views for historical analysis
- Heatmaps indicating areas of repeated suspicious activity

#### Search and Filter Capabilities
- Advanced filtering options (vessel type, location, date, incident type)
- Quick search capability for specific vessels or incidents
- Exportable reports for offline analysis and evidence submission

#### Sharing and Collaboration
- Secure, shareable links for incident reports
- Customizable alert system for real-time notifications (email, SMS, push notifications)
- User-friendly natural language summaries of detected threats and recommended actions

---

### Users

#### Maritime Security Forces
- Real-time monitoring and alerts
- Actionable intelligence for interdiction and enforcement

#### Coastal Communities
- Simple reporting tools for local fishermen and community members
- Enhanced awareness and capacity for organized community action

#### Port Authorities
- Improved monitoring of vessel activities
- Coordinated response with maritime enforcement agencies

#### Coalition Forces
- Shared intelligence and collaboration capabilities
- Enhanced situational awareness for joint maritime operations

## Docker Deployment

1. Build and push the Docker image (multi-platform):
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t ksiadz/temporal-worker:latest --push temporals/base
```

Or for a specific platform:
```bash
docker buildx build --platform linux/amd64 -t ksiadz/temporal-worker:latest --push temporals/base
```

2. Run the container locally:
```bash
docker run -e TEMPORAL_API_KEY=your-api-key ksiadz/temporal-worker:latest
```

## Kubernetes Deployment

### Manual Deployment

1. Create the temporal namespace:
```bash
kubectl apply -f manifests/namespace.yaml
```

2. Create the secret with your API key:
```bash
kubectl create secret generic temporal-worker-secrets \
  --namespace temporal \
  --from-literal=TEMPORAL_API_KEY=your-api-key \
  --dry-run=client -o yaml | kubectl apply -f -
```

3. Apply all manifests:
```bash
kubectl apply -k manifests/
```

### GitOps Deployment (Flux/ArgoCD)


