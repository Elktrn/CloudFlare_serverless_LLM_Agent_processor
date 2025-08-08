from workers import Response
import json
import datetime

async def on_fetch(request, env):
    if request.method == "POST":
        payload = await request.json()
        jsond = await env.itinerarykv.get(f"job_{payload.jobId}")
        parsed_data = json.loads(jsond)
        try:
                # Mock LLM call for itinerary generation
                itinerary = [
                    {
                        "day": 1,
                        "theme": f"Historical {parsed_data['destination']}",
                        "activities": [
                            {"time": "Morning", "description": "Visit museum", "location": "Museum"},
                            {"time": "Afternoon", "description": "Explore historic district", "location": "District"},
                            {"time": "Evening", "description": "Dinner at local restaurant", "location": "Downtown"}
                        ]
                    }
                ]
                parsed_data["itinerary"] = itinerary
                parsed_data["status"] = "completed"
                parsed_data["completedAt"] = str(datetime.datetime.now())
        except Exception as e:
            parsed_data["status"] = "failed"
            parsed_data["error"] = str(e)

        # Update KV with results
        json_data = json.dumps(parsed_data)
        await env.itinerarykv.put(f"job_{payload.jobId}", json_data)
        print(f"Processed job_{payload.jobId}: {parsed_data['status']}")
        
        return Response(json.dumps({"status": "success"}), status=200)
    else:
        return Response(json.dumps({"error": "Invalid request"}), status=400)