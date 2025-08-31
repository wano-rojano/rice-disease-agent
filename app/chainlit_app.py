import os, json
import httpx
import chainlit as cl
from uuid import uuid4
from dotenv import load_dotenv
import logging

load_dotenv()

if os.getenv("ENVIRONMENT") == "production":
    BASE_URL = "https://rice-disease-agent.onrender.com"
else:
    BASE_URL = os.getenv("A2A_BASE_URL", "http://localhost:10000")

logger = logging.getLogger(__name__)

def format_response(text: str) -> str:
    """Format the agent response for better readability."""
    replacements = {
        "Diagnosis:": "🔬 **Diagnosis:**",
        "Differentials:": "🔍 **Differentials:**", 
        "Immediate actions:": "⚡ **Immediate Actions:**",
        "Integrated management:": "🌾 **Integrated Management:**",
        "Monitoring:": "👁️ **Monitoring:**",
        "Information needed:": "❓ **Information Needed:**",
        "Sources:": "📚 **Sources:**"
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

@cl.on_chat_start
async def on_chat_start():
    httpx_client = httpx.AsyncClient(
        timeout=httpx.Timeout(180.0),
        transport=httpx.AsyncHTTPTransport(retries=3),
    )
    cl.user_session.set("httpx", httpx_client)
    
    actions = [
        cl.Action(name="common_diseases", value="common_diseases", label="🦠 Common Rice Diseases", payload={}),
        cl.Action(name="symptoms", value="symptoms", label="🔍 Identify Symptoms", payload={}),
        cl.Action(name="management", value="management", label="🌾 IPM Strategies", payload={}),
    ]
    
    await cl.Message(
        content="🌾 **Rice Disease Agent** ready! Ask me about rice pathology, diseases, or integrated pest management.\n\n💡 *I prioritize evidence from the [Rice Diseases Online Resource](https://rice-diseases.irri.org/contents), with web search and academic papers as backup.*",
        actions=actions
    ).send()

# Fixed action callbacks with correct parameter names
@cl.action_callback("common_diseases")
async def on_common_diseases(action):
    await cl.Message(content="What are the most common rice diseases in your region? Please mention your location (country/region) and growing conditions (upland/lowland, irrigated/rainfed).").send()

@cl.action_callback("symptoms") 
async def on_symptoms(action):
    await cl.Message(content="Describe the symptoms you're seeing:\n• **Location**: Country/region and field type\n• **Growth stage**: Seedling, tillering, heading, etc.\n• **Symptoms**: Leaf spots, wilting, discoloration, lesion details\n• **Weather**: Recent humidity, rain, temperature").send()

@cl.action_callback("management")
async def on_management(action):
    await cl.Message(content="What specific disease would you like IPM recommendations for? Include your region and current management practices if possible.").send()

@cl.on_message
async def on_message(message: cl.Message):
    httpx_client: httpx.AsyncClient = cl.user_session.get("httpx")
    
    thinking_msg = cl.Message(content="🤔 Analyzing your rice disease query...")
    await thinking_msg.send()
    
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": message.content}],
                "message_id": uuid4().hex,
            }
        },
        "id": str(uuid4())
    }
    
    context_id = cl.user_session.get("context_id")
    if context_id:
        payload["params"]["context_id"] = context_id
    
    try:
        resp = await httpx_client.post(f"{BASE_URL}/", json=payload)
        resp.raise_for_status()
        data = resp.json()
        await thinking_msg.remove()

        text = None
        task_id = None
        new_context_id = None
        
        if "result" in data:
            result = data["result"]
            
            if isinstance(result, dict):
                task_id = result.get("id")
                new_context_id = result.get("contextId")
                
                # Extract from artifacts (completed tasks)
                if "artifacts" in result and result.get("status", {}).get("state") == "completed":
                    artifacts = result["artifacts"]
                    for artifact in artifacts:
                        if artifact.get("name") == "result" and "parts" in artifact:
                            parts = artifact["parts"]
                            texts = [p.get("text") for p in parts if p.get("kind") == "text" and p.get("text")]
                            text = "\n".join(texts) if texts else None
                            if text:
                                break
                
                # Fallback: extract from status message
                if not text and "status" in result and "message" in result["status"]:
                    status_msg = result["status"]["message"]
                    if isinstance(status_msg, dict) and "parts" in status_msg:
                        parts = status_msg.get("parts", [])
                        texts = [p.get("text") for p in parts if p.get("kind") == "text" and p.get("text")]
                        text = "\n".join(texts) if texts else None
                        
        # Check for JSON-RPC error
        if not text and "error" in data:
            error = data["error"]
            text = f"❌ Server error: {error.get('message', 'Unknown error')}"

        # Send response with formatting
        if text:
            if "error processing" in text.lower() or "try again" in text.lower():
                await cl.Message(content=f"⚠️ {text}\n\n💡 **Try asking more specific questions like:**\n• What causes leaf blast in rice?\n• How to manage bacterial leaf blight in irrigated systems?\n• Symptoms of false smut in West Africa").send()
            else:
                formatted_text = format_response(text)
                await cl.Message(content=formatted_text).send()
        else:
            await cl.Message(content=f"Response received but couldn't parse text. Raw data:\n```json\n{json.dumps(data, indent=2)}\n```").send()

        # Save context
        if task_id:
            cl.user_session.set("task_id", task_id)
        if new_context_id:
            cl.user_session.set("context_id", new_context_id)
        
    except httpx.HTTPError as e:
        await thinking_msg.remove()
        await cl.Message(content=f"❌ Request failed: {e}").send()
    except Exception as e:
        await thinking_msg.remove()
        logger.error(f"Unexpected error: {e}")
        await cl.Message(content=f"❌ Unexpected error: {e}").send()

@cl.on_chat_end
async def on_chat_end():
    httpx_client: httpx.AsyncClient = cl.user_session.get("httpx")
    if httpx_client:
        await httpx_client.aclose()