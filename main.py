from workers import Response
import json
import datetime
import asyncio
import urllib.request
from workers import fetch
async def on_fetch(request, env):
    if request.method == "POST":
        payload = await request.json()
        jsond = await env.itinerarykv.get(f"job_{payload.jobId}")
        parsed_data = json.loads(jsond)
        try:
                system_prompt="""Task: Fill in the "FILL" placeholders in the provided itinerary JSON for the given city.

Instructions:

    You will be given a city name, for example, "Paris."

    The itinerary JSON will contain one or more days, each with a "theme" and a list of "activities." Each activity specifies a "time" (Morning, Afternoon, Evening), a "description," and a "location."

    For each day:
        If any "location" fields in the activities are already provided (i.e., not "FILL"), choose a theme from the following options that best fits those locations: 'historical', 'modern', 'art', 'musical', 'cultural'.
        If all "location" fields are "FILL," choose any theme from the options above.
        Set the "theme" to the chosen theme with the first letter capitalized, followed by the city name (e.g., "Historical Paris").

    For each activity in the day:
        If the "location" is "FILL," select a location in the city that fits the day's theme and provide a one-sentence description of an activity to do at that location during the specified time.
        If the "location" is already provided, provide a one-sentence description of an activity to do at that location during the specified time, ensuring it aligns with the day's theme.
        Ensure that the description is concise and relevant to both the theme and the time of day.

    Only modify the "FILL" placeholders; leave all other fields unchanged.

    Only Provide the completed JSON with all "FILL" placeholders appropriately replaced. do not add any prefix, postfix, apologies or explanation only the desiered output starting with [ and end with ]. 

Example Input:

City: Paris
[
{
  "day": 1,
  "theme": "FILL",
  "activities": [
    {
      "time": "Morning",
      "description": "FILL",
      "location": "FILL"
    },
    {
      "time": "Afternoon",
      "description": "FILL",
      "location": "FILL"
    },
    {
      "time": "Evening",
      "description": "FILL",
      "location": "FILL"
    }
  ]
},
{
  "day": 2,
  "theme": "FILL",
  "activities": [
    {
      "time": "Morning",
      "description": "FILL",
      "location": "Musée d'Orsay"
    },
    {
      "time": "Afternoon",
      "description": "FILL",
      "location": "FILL"
    },
    {
      "time": "Evening",
      "description": "FILL",
      "location": "FILL"
    }
  ]
}
]
Expected Output:
[
{
  "day": 1,
  "theme": "Historical Paris",
  "activities": [
    {
      "time": "Morning",
      "description": "Visit the Louvre Museum. Pre-book tickets to avoid queues.",
      "location": "Louvre Museum"
    },
    {
      "time": "Afternoon",
      "description": "Explore the Notre-Dame Cathedral area and walk along the Seine.",
      "location": "Île de la Cité"
    },
    {
      "time": "Evening",
      "description": "Dinner in the Latin Quarter.",
      "location": "Latin Quarter"
    }
  ]
},
{
  "day": 2,
  "theme": "Art Paris",
  "activities": [
    {
      "time": "Morning",
      "description": "Discover Impressionist masterpieces at the Musée d'Orsay.",
      "location": "Musée d'Orsay"
    },
    {
      "time": "Afternoon",
      "description": "Explore contemporary art at the Centre Pompidou.",
      "location": "Centre Pompidou"
    },
    {
      "time": "Evening",
      "description": "Stroll through Montmartre and visit the Sacré-Cœur Basilica.",
      "location": "Montmartre"
    }
  ]
}
]"""

                api_url = "https://api.openai.com/v1/chat/completions"

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {env.OPENAI_API_KEY}"
                }

                openai_payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{parsed_data["destination"]}\n{payload.iten}"}
                    ]
                }
                
                # Use the imported fetch function
                response = await fetch(api_url, method="POST", headers=headers, body=json.dumps(openai_payload))

                if response.status != 200:
                    error_text = await response.text()
                    parsed_data["status"] = "failed"
                    parsed_data["error"] = str(error_text)
                    parsed_data["itinerary"] = payload.iten
                    await env.itinerarykv.put(f"job_{payload.jobId}", json.dumps(parsed_data))
                    return Response(f"Error from OpenAI API: {response.status} - {error_text}", status=response.status)

                response_data = await response.json()
                
                itinerary = response_data["choices"][0]["message"]["content"]
                #use the following commented code to fabricate an itinerary
                # itinerary = [
                #     {
                #         "day": 1,
                #         "theme": f"Historical ",
                #         "activities": [
                #             {"time": "Morning", "description": "Visit museum", "location": "Museum"},
                #             {"time": "Afternoon", "description": "Explore historic district", "location": "District"},
                #             {"time": "Evening", "description": "Dinner at local restaurant", "location": "Downtown"}
                #         ]
                #     }
                # ]
                parsed_data["itinerary"] = itinerary
                parsed_data["status"] = "completed"
                parsed_data["completedAt"] = str(datetime.datetime.now())
        except Exception as e:
            parsed_data["status"] = "failed"
            parsed_data["error"] = str(e)

        # Update KV with results
        await env.itinerarykv.put(f"job_{payload.jobId}", json.dumps(parsed_data))
        
        return Response(json.dumps({"status": f"success "}), status=200)
    else:
        return Response(json.dumps({"error": "Invalid request"}), status=400)