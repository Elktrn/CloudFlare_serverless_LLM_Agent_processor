from workers import Response
import json
import datetime

async def on_fetch(request, env):
    if request.method == "POST" and request.url.endswith("/process"):
        try:
            payload = await request.json()
            job_id = payload.get("jobId")
            if not job_id:
                return Response(json.dumps({"error": "No jobId provided"}), status=400)

            # Fetch job data from KV
            jsond = await env.itinerarykv.get(f"job_{job_id}")
            if not jsond:
                return Response(json.dumps({"error": "Job not found"}), status=404)
            parsed_data = json.loads(jsond)

            if parsed_data["status"] == "pending":
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
                await env.itinerarykv.put(f"job_{job_id}", json_data)
                print(f"Processed job_{job_id}: {parsed_data['status']}")
            
            return Response(json.dumps({"status": "success"}), status=200)
        except Exception as e:
            return Response(json.dumps({"error": f"Processing failed: {str(e)}"}), status=400)
    else:
        return Response(json.dumps({"error": "Invalid request"}), status=400)