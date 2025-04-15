# Inside backend/ai_handler.py
import os
import google.generativeai as genai
from langdetect import detect, LangDetectException
import time
import json # Import json module

# --- Configure AI ---
API_KEY = os.getenv("GEMINI_API_KEY")
model = None # Initialize model variable

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash-latest') # Use appropriate model
        print("AI Handler: Gemini model configured.")
    except Exception as e:
        print(f"AI Handler: Error configuring Gemini: {e}")
        model = None
else:
    print("AI Handler: GEMINI_API_KEY not found. AI functions disabled.")

# --- Helper Functions ---

def detect_language(text):
    """Detects language using langdetect."""
    if not text or not isinstance(text, str) or len(text.strip()) < 20:
         print("Warning: Not enough text to reliably detect language, defaulting to English.")
         return "en"
    try:
        lang = detect(text[:500]) # Detect based on first 500 chars
        print(f"Detected language: {lang}")
        return lang
    except LangDetectException as e: # Catch specific exception
        print(f"Could not detect language: {e}, defaulting to English.")
        return "en"
    except Exception as e: # Catch any other unexpected errors
        print(f"An unexpected error occurred during language detection: {e}")
        return "en"

def call_gemini_api(prompt_text, retry_count=2, delay=5):
    """ Helper function to call the API with retry logic. """
    if not model:
         print("Error: AI Model not configured or API key test failed.")
         return None # Indicate failure clearly
    try:
         # Configure safety settings and generation parameters
         safety_settings=[
              {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
              {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
              {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
              {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
         ]
         generation_config = genai.types.GenerationConfig(
             temperature=0.7, # Adjust creativity vs factualness
             # max_output_tokens=2048 # Increase if needed for complex JSON
             response_mime_type="application/json" # Request JSON output directly if supported
         )

         print(f"\n--- Sending Prompt to AI (length: {len(prompt_text)} chars) ---")
         # print(f"Prompt Snippet:\n{prompt_text[:500]}...") # Uncomment for debugging prompts

         response = model.generate_content(
             prompt_text,
             generation_config=generation_config,
             safety_settings=safety_settings
         )
         print("--- Received AI Response ---")

         # Handle potential blocks or empty responses
         if not response.candidates:
             print("Warning: AI response blocked or empty. Check safety settings or prompt.")
             if hasattr(response, 'prompt_feedback') and response.prompt_feedback: print(f"Prompt Feedback: {response.prompt_feedback}")
             # Return a structured error
             return json.dumps({"error": "AI response blocked or empty.", "details": str(getattr(response, 'prompt_feedback', 'N/A'))})

         # Check if text attribute exists and has content
         if hasattr(response, 'text') and response.text:
             # Assuming the response text IS the JSON string
             return response.text
         else:
             print("Warning: No text parts found in AI response or response.text is empty.")
             # Return a structured error
             return json.dumps({"error": "AI generated empty or non-text response."})

    except Exception as e:
         print(f"Error calling AI API: {e}")
         if retry_count > 0:
             print(f"Retrying AI call in {delay} seconds... ({retry_count} retries left)")
             time.sleep(delay)
             return call_gemini_api(prompt_text, retry_count - 1, delay * 2) # Exponential backoff
         else:
             print("AI call failed after multiple retries.")
             # Return a structured error in JSON format
             return json.dumps({"error": f"AI call failed after multiple retries: {e}"})


# === Shopify SEO AI Function ===
def get_shopify_seo_ai(scraped_data, target_language):
    """ Generates complex SEO analysis for Shopify, expecting JSON output. """
    if not model: return {"error": "AI Model not configured"}
    if not scraped_data or scraped_data.get("error"):
        return {"error": f"Invalid or missing scraped data provided: {scraped_data.get('error', 'N/A')}"}

    lang_name = "Romanian" if target_language == "ro" else "English"
    print(f"--- Getting Shopify SEO AI analysis in {lang_name} ---")

    # Prepare snippets of complex data for the prompt
    headings_summary = {k: v[:2] for k, v in scraped_data.get('headings', {}).items() if v} # Show first 2 of each level
    alt_texts_summary = scraped_data.get('alt_texts', [])[:5] # Show first 5 alt texts
    schema_summary = [s.get('@type', 'Unknown Type') for s in scraped_data.get('schema_data', [])][:3] # Show first 3 schema types
    links_summary = scraped_data.get('links', {})

    prompt = f"""
    Analyze the following data scraped from a potential Shopify page ({scraped_data.get('url', 'N/A')}) for SEO optimization opportunities in {lang_name}.

    **Scraped Data:**
    - Title: {scraped_data.get('title', 'N/A')}
    - Meta Description: {scraped_data.get('meta_description', 'N/A')}
    - H1 Heading: {scraped_data.get('h1', 'N/A')}
    - Headings Structure (Sample): {json.dumps(headings_summary)}
    - Image Alt Texts (Sample): {json.dumps(alt_texts_summary)}
    - Detected Schema Types (Sample): {json.dumps(schema_summary)}
    - Link Counts: Internal: {links_summary.get('internal', 'N/A')}, External: {links_summary.get('external', 'N/A')}
    - Content Snippet: "{scraped_data.get('content_snippet', 'N/A')[:500]}..."

    **Analysis Tasks (Perform in {lang_name}):**

    1.  **Core SEO Elements Critique & Suggestions:**
        * Critique the current Title (length, clarity, keywords). Suggest 1 improved SEO Title (max 60 chars), explaining the reasoning.
        * Critique the current Meta Description (length, clarity, call-to-action, keywords). Suggest 1 improved Meta Description (max 155 chars), explaining the reasoning.
        * Analyze the H1 heading. Is it effective? Suggest an improvement if necessary.

    2.  **Content & Keywords:**
        * Based on the headings and content snippet, identify the main topic and suggest 5-7 relevant keywords (mix of short/long-tail).
        * Suggest 2 specific Shopify blog post titles relevant to the scraped content that could drive traffic.

    3.  **On-Page & Technical Considerations:**
        * Based on the sample alt texts, provide 1 specific recommendation for improving image SEO on this page or Shopify stores in general.
        * Based on the detected schema types (or lack thereof), recommend the MOST appropriate Schema.org type (e.g., Product, Article, CollectionPage) for this page and list 3 essential properties to include. If schema exists, briefly evaluate its type.
        * Provide 2 actionable, technical SEO tips relevant for Shopify stores (e.g., related to site speed, mobile-friendliness, URL structure, duplicate content).

    **Output Format:**
    Generate your response *exclusively* as a single, valid JSON object. Use the following structure precisely. All string values within the JSON should be in {lang_name}.

    ```json
    {{
      "analysis_language": "{target_language}",
      "core_seo": {{
        "title_critique": "[Your critique of the current title]",
        "suggested_title": "[Your suggested title]",
        "title_reasoning": "[Reasoning for suggested title]",
        "description_critique": "[Your critique of the current meta description]",
        "suggested_description": "[Your suggested description]",
        "description_reasoning": "[Reasoning for suggested description]",
        "h1_analysis": "[Your analysis of the H1 heading]",
        "suggested_h1": "[Suggested H1 only if improvement needed, else null]"
      }},
      "content_keywords": {{
        "main_topic": "[Identified main topic]",
        "suggested_keywords": ["[keyword1", "keyword2", "...", "keyword7"],
        "blog_post_ideas": ["[Blog title idea 1]", "[Blog title idea 2]"]
      }},
      "on_page_technical": {{
        "image_seo_tip": "[Specific alt text/image SEO recommendation]",
        "schema_recommendation": {{
          "suggested_type": "[Recommended Schema.org type e.g., Product]",
          "required_properties": ["[property1", "property2", "property3"],
          "current_schema_evaluation": "[Brief evaluation if schema was found, else null]"
        }},
        "technical_tips": ["[Technical SEO Tip 1]", "[Technical SEO Tip 2]"]
      }}
    }}
    ```

    --- End of Instructions ---
    """

    raw_json_response = call_gemini_api(prompt)

    if not raw_json_response:
        return {"error": "Failed to get response from AI after retries."}

    try:
        # Parse the JSON response from the AI
        parsed_results = json.loads(raw_json_response)
        if "error" in parsed_results: # Handle errors returned *within* the JSON
             print(f"AI returned an error in its JSON response: {parsed_results['error']}")
             # Optionally add more details if available: parsed_results.get('details')
             return {"error": f"AI Error: {parsed_results['error']}"}

        print("--- Shopify SEO AI analysis generated and parsed successfully ---")
        return parsed_results
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON response from AI: {e}")
        print(f"Raw AI Response Snippet: {raw_json_response[:500]}") # Log snippet for debugging
        return {"error": "Failed to parse AI response as JSON.", "raw_response_snippet": raw_json_response[:500]}
    except Exception as e:
        print(f"Error processing AI response: {e}")
        return {"error": f"Unexpected error processing AI response: {e}"}


# === Social Media AI Function ===
def get_social_media_ai(platform, topic, keywords, target_language):
    """ Generates complex social media content ideas, expecting JSON output. """
    if not model: return {"error": "AI Model not configured"}
    if not topic: return {"error": "Topic/description input is required"}

    lang_name = "Romanian" if target_language == "ro" else "English"
    print(f"--- Getting Social Media AI suggestions for {platform} about '{topic[:50]}...' in {lang_name} ---")

    prompt = f"Act as a creative social media marketing expert specializing in {platform.upper()}."
    prompt += f"\nGenerate content ideas in {lang_name} for **{platform.upper()}** based on the following:"
    prompt += f"\n- Main Topic/Product: '{topic}'"
    if keywords:
        prompt += f"\n- Keywords: {keywords}"
    prompt += "\n\n**Content Requirements:**\n"

    # Platform-specific instructions requesting more detail and JSON output
    if platform == "youtube":
        prompt += """
        - Generate 2 distinct YouTube video concepts:
            - For each concept, provide:
                - An engaging Title (max 70 chars).
                - A brief Hook (first 5-10 seconds idea).
                - A 3-4 bullet point Outline covering key segments.
                - A specific Call-to-Action.
                - A relevant Thumbnail concept description (visual idea).
        - Suggest 5 relevant YouTube tags/keywords.
        - Justify *why* one of the video concepts is particularly suited for YouTube engagement.

        **Output Format:** Respond *only* with a valid JSON object using this structure:
        ```json
        {
          "platform": "youtube",
          "language": "%s",
          "concepts": [
            {
              "title": "[Generated Title 1]",
              "hook": "[Hook idea 1]",
              "outline": ["[Point 1.1]", "[Point 1.2]", "[Point 1.3]"],
              "call_to_action": "[CTA 1]",
              "thumbnail_concept": "[Thumbnail description 1]"
            },
            {
              "title": "[Generated Title 2]",
              "hook": "[Hook idea 2]",
              "outline": ["[Point 2.1]", "[Point 2.2]", "[Point 2.3]", "[Point 2.4]"],
              "call_to_action": "[CTA 2]",
              "thumbnail_concept": "[Thumbnail description 2]"
            }
          ],
          "suggested_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
          "justification": "[Explanation why one concept is well-suited]"
        }
        ```
        """ % target_language
    elif platform == "instagram": # Assuming Reels/Posts focus
        prompt += """
        - Generate 2 distinct Instagram post/Reel ideas:
            - For each idea, provide:
                - A hook-focused Caption Idea (under 30 words).
                - A Visual Concept (e.g., type of image, Reel style, trending audio suggestion).
                - A specific Call-to-Action.
        - Suggest 1 set of 7 relevant Hashtags (mix broad, niche, specific).
        - Provide 1 Instagram Story idea (e.g., poll, Q&A, behind-the-scenes) related to the topic.
        - Briefly explain how one idea uses a common engagement tactic (e.g., question, user-generated content prompt).

        **Output Format:** Respond *only* with a valid JSON object using this structure:
        ```json
        {
          "platform": "instagram",
          "language": "%s",
          "post_ideas": [
            {
              "caption_idea": "[Generated Caption 1]",
              "visual_concept": "[Visual/audio concept 1]",
              "call_to_action": "[CTA 1]"
            },
            {
              "caption_idea": "[Generated Caption 2]",
              "visual_concept": "[Visual/audio concept 2]",
              "call_to_action": "[CTA 2]"
            }
          ],
          "suggested_hashtags": ["#hashtag1", "#hashtag2", ..., "#hashtag7"],
          "story_idea": "[Instagram story idea description]",
          "engagement_tactic_explanation": "[Explanation of engagement tactic used]"
        }
        ```
        """ % target_language
    elif platform == "pinterest":
         prompt += """
         - Generate 2 distinct Pin concepts:
             - For each concept, provide:
                 - An SEO-optimized Pin Title (keyword-rich).
                 - A compelling Pin Description (1-3 sentences, include keywords and CTA).
                 - A visual description (what the Pin image/video should show).
         - Suggest 3 relevant Pinterest Board names.
         - Explain why one of the Pin concepts is visually appealing for Pinterest.

         **Output Format:** Respond *only* with a valid JSON object using this structure:
         ```json
         {
           "platform": "pinterest",
           "language": "%s",
           "pin_concepts": [
             {
               "title": "[Generated Title 1]",
               "description": "[Generated Description 1]",
               "visual_description": "[Visual description 1]"
             },
             {
               "title": "[Generated Title 2]",
               "description": "[Generated Description 2]",
               "visual_description": "[Visual description 2]"
             }
           ],
           "suggested_boards": ["BoardName1", "BoardName2", "BoardName3"],
           "visual_appeal_explanation": "[Explanation of visual appeal]"
         }
         ```
         """ % target_language
    else:
        return {"error": f"Unsupported social platform: {platform}"}

    prompt += "\n--- End of Instructions ---"

    raw_json_response = call_gemini_api(prompt)

    if not raw_json_response:
       return {"error": f"Failed to get {platform} response from AI after retries."}

    try:
        # Parse the JSON response from the AI
        parsed_results = json.loads(raw_json_response)
        if "error" in parsed_results: # Handle errors returned *within* the JSON
            print(f"AI returned an error in its JSON response: {parsed_results['error']}")
            return {"error": f"AI Error for {platform}: {parsed_results['error']}"}

        print(f"--- {platform.capitalize()} AI suggestions generated and parsed successfully ---")
        # Add back platform/topic for context if needed by frontend, though it's in the JSON now
        # parsed_results['platform_requested'] = platform
        # parsed_results['topic_used'] = topic
        return parsed_results
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON response from AI for {platform}: {e}")
        print(f"Raw AI Response Snippet: {raw_json_response[:500]}") # Log snippet
        return {"error": f"Failed to parse {platform} AI response as JSON.", "raw_response_snippet": raw_json_response[:500]}
    except Exception as e:
        print(f"Error processing AI response for {platform}: {e}")
        return {"error": f"Unexpected error processing {platform} AI response: {e}"}